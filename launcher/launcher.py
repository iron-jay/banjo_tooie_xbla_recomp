"""Banjo-Tooie PC port launcher.

Takes your own legally-owned Banjo-Tooie XBLA package (the STFS 'LIVE'
container from your Xbox 360 profile), extracts the game data from it, and
launches the recompiled banjotooie.exe pointed at that data - no
compilation happens here, the recompiled executable is prebuilt and ships
alongside this launcher (see README.md in this folder for why).

Usage: python launcher.py   (or run the packaged launcher.exe)
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox

from stfs_extract import RAWFILES_NAMES, StfsPackage


def _app_dir() -> str:
    """Folder the launcher lives in - and where game/, game_data/, saves/ and
    the config are kept. When frozen by PyInstaller this is the directory that
    holds the .exe, NOT the temporary _MEIPASS unpack dir (so player data
    persists next to the exe wherever they put it)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _resource_dir() -> str:
    """Folder holding bundled read-only payload - _MEIPASS when frozen, else
    the source dir."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


IS_WINDOWS = os.name == "nt"
# The recompiled game binary: banjotooie.exe on Windows, banjotooie on Linux.
EXE_NAME = "banjotooie.exe" if IS_WINDOWS else "banjotooie"
# CMake build-tree platform dir, for the run-from-source dev fallback.
_BUILD_PLATFORM = "win-amd64" if IS_WINDOWS else "linux-amd64"

APP_DIR = _app_dir()
# Everything the launcher generates lives under ONE folder next to the launcher,
# keeping the game/ , game_data/ , saves/ , config structure inside it - so the
# launcher's directory stays tidy (just the launcher + this one data folder).
DATA_DIR = os.path.join(APP_DIR, "BanjoTooie-Data")
CONFIG_PATH = os.path.join(DATA_DIR, "launcher_config.xml")
GAME_DIR = os.path.join(DATA_DIR, "game")         # game binary + its libs live here
GAME_DATA_DIR = os.path.join(DATA_DIR, "game_data")
SAVES_DIR = os.path.join(DATA_DIR, "saves")
EXTRACT_MARKER = os.path.join(GAME_DATA_DIR, ".extracted_ok")
# SHA-256 of xbla/files/default.xex from the exact XBLA build this port was
# recompiled against. banjotooie-recomp/generated/ + overrides.toml (the
# recompiled function table and manual fixups) are only valid for this one
# executable - a different region/revision could lay out code completely
# differently, which the precompiled functions would silently mismatch rather
# than fail loudly (see the "hash check" conversation in CLAUDE.md history).
# Checked right after extraction, before the data is trusted.
TESTED_XEX_SHA256 = "4b512ae9f4412c246fe40a8b07b9d2932e1d18259dacb830991d7dbf827367a5"
# Game binaries bundled inside a frozen build (empty when running from source).
PAYLOAD_DIR = os.path.join(_resource_dir(), "payload")
# App/window icon (bundled into the frozen build; also present in source).
ICON_PNG = os.path.join(_resource_dir(), "banjotooie.png")

# Where to find the game binary. Prefer the provisioned/bundled copy in game/,
# then a flat copy next to the launcher, then the dev build tree (Release
# before Debug - see CLAUDE.md "Performance (Debug vs Release)").
EXE_CANDIDATES = [
    os.path.join(GAME_DIR, EXE_NAME),
    os.path.join(APP_DIR, EXE_NAME),
    os.path.join(APP_DIR, "..", "banjotooie-recomp", "out", "build",
                 f"{_BUILD_PLATFORM}-release", EXE_NAME),
    os.path.join(APP_DIR, "..", "banjotooie-recomp", "out", "build",
                 f"{_BUILD_PLATFORM}-debug", EXE_NAME),
]


def _payload_stamp(dir_path: str) -> str | None:
    """Read payload_version.txt from dir_path (written by build_release.py);
    None if absent (older launcher builds didn't ship one)."""
    try:
        with open(os.path.join(dir_path, "payload_version.txt"), "r") as f:
            return f.read().strip() or None
    except OSError:
        return None


def provision_game() -> str | None:
    """When the launcher bundles the game binaries (a frozen release build),
    copy them into game/ next to the launcher, so the game binary and its
    libraries sit together in a persistent, writable folder. Runs on first
    launch AND whenever the bundled payload_version.txt stamp differs from the
    provisioned copy's - so a launcher carrying updated game binaries refreshes
    an existing install instead of silently keeping the old ones. No-op when
    running from source (no bundled payload). Returns an error message on
    failure, else None."""
    if not os.path.isdir(PAYLOAD_DIR):
        return None  # running from source - the dev build tree is used instead
    if os.path.exists(os.path.join(GAME_DIR, EXE_NAME)):
        bundled = _payload_stamp(PAYLOAD_DIR)
        if bundled is not None and bundled == _payload_stamp(GAME_DIR):
            return None  # provisioned and up to date
        # else: stamp differs, or a pre-stamp install -> re-provision below
    try:
        os.makedirs(GAME_DIR, exist_ok=True)
        for name in os.listdir(PAYLOAD_DIR):
            src = os.path.join(PAYLOAD_DIR, name)
            if os.path.isfile(src):
                dst = os.path.join(GAME_DIR, name)
                shutil.copy2(src, dst)
                # PyInstaller data-bundling can drop the exec bit; the game
                # binary and shared objects need it back on Linux.
                if not IS_WINDOWS and (name == EXE_NAME or name.endswith(".so")):
                    os.chmod(dst, 0o755)
    except OSError as e:
        return f"Could not set up the game files next to the launcher:\n{e}"
    return None

# --- Theme (Banjo-Tooie honeycomb: warm dark background, gold + green accents) ---
WIN_W, WIN_H = 580, 520
CONTENT_W = WIN_W - 2 * 22          # inner width inside the 22px content padding

# Segoe UI is Windows-only; DejaVu Sans ships on virtually every Linux distro
# (including SteamOS), so the launcher looks right on the Steam Deck too.
UI_FONT = "Segoe UI" if IS_WINDOWS else "DejaVu Sans"

BG        = "#241d18"   # window background (warm near-black)
ENTRY_BG  = "#3a2f26"   # inset field background
TEXT      = "#f3e7d4"   # primary cream text
MUTED     = "#b0a08c"   # secondary / hint text
ERR       = "#e8897a"   # error text
SEP       = "#4a3c2e"   # divider line

GOLD_TOP  = "#ffcf55"   # header gradient top
GOLD_BOT  = "#eba62a"   # header gradient bottom
HEX_LINE  = "#ffe09a"   # decorative hexagon outline in header
HEAD_TEXT = "#3a2810"   # dark text over the gold header

GOLD      = "#f2b632"   # gold button
GOLD_HI   = "#ffca4d"   # gold button hover
GOLD_TEXT = "#2c1f0c"   # text on gold

GREEN     = "#4f9d3a"   # play button
GREEN_HI  = "#5cb444"   # play button hover
GREEN_TXT = "#ffffff"   # text on green

TROUGH    = "#3a2f26"   # progress-bar trough
BAR_FILL  = "#ffca4d"   # progress-bar fill

DISABLED_BG = "#463b30"
DISABLED_FG = "#8a7e70"


def load_config() -> dict:
    """Read the launcher config (XML). Returns keys: package_path (str),
    auto_play (bool). A missing or corrupt file falls back to defaults."""
    cfg = {"package_path": "", "auto_play": False}
    if os.path.exists(CONFIG_PATH):
        try:
            root = ET.parse(CONFIG_PATH).getroot()
            pkg = root.findtext("package_path")
            if pkg is not None:
                cfg["package_path"] = pkg.strip()
            ap = root.findtext("auto_play")
            if ap is not None:
                cfg["auto_play"] = ap.strip().lower() in ("1", "true", "yes", "on")
        except (ET.ParseError, OSError):
            pass
    return cfg


def save_config(cfg: dict) -> None:
    """Write the launcher config as XML (creating the data folder if needed).
    Edit auto_play here to true/false to turn auto-play on or off by hand."""
    root = ET.Element("launcher")
    ET.SubElement(root, "package_path").text = str(cfg.get("package_path", ""))
    ET.SubElement(root, "auto_play").text = "true" if cfg.get("auto_play") else "false"
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    os.makedirs(DATA_DIR, exist_ok=True)
    tree.write(CONFIG_PATH, encoding="utf-8", xml_declaration=True)


def find_game_exe() -> str | None:
    for candidate in EXE_CANDIDATES:
        path = os.path.abspath(candidate)
        if os.path.exists(path):
            return path
    return None


def _hash_file(path: str) -> str:
    """SHA-256 of a file's contents, streamed (the .xex is only a few MB, but
    no reason to load it all into memory at once)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _game_data_present() -> bool:
    """True if game_data/ actually still has what the game needs to run right
    now - not just whether the .extracted_ok marker exists. The marker lives
    inside game_data/ itself, so it only reflects reality at the moment
    extraction finished; if a player deletes or moves files under game_data/
    afterward (freeing space, troubleshooting, a half-finished manual cleanup,
    etc.) without touching the marker, a marker-only check would still claim
    "ready to play" right up until the game itself fails partway through
    boot. Check for the specific files the game actually opens instead."""
    if not os.path.exists(EXTRACT_MARKER):
        return False
    if not os.path.isfile(os.path.join(GAME_DATA_DIR, "default.xex")):
        return False
    rawfiles_dir = os.path.join(GAME_DATA_DIR, "RAWFiles")
    return all(os.path.isfile(os.path.join(rawfiles_dir, name)) for name in RAWFILES_NAMES)


def _round_rect_points(x1, y1, x2, y2, r):
    """Flat point list for a smooth-cornered rounded rectangle polygon."""
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


class RoundedButton(tk.Canvas):
    """A flat, rounded, color-fillable button drawn on a Canvas.

    ttk's native Windows button theme ignores most color options, so the
    buttons are hand-drawn to get a consistent themed look with hover states.
    """

    def __init__(self, parent, text, command, width, height, *,
                 bg, bg_hover, fg, font=(UI_FONT, 11, "bold"), radius=14):
        super().__init__(parent, width=width, height=height, bg=BG,
                         highlightthickness=0, bd=0)
        self._cmd = command
        self._bg, self._bg_hover, self._fg = bg, bg_hover, fg
        self._enabled = True
        self._rect = self.create_polygon(
            _round_rect_points(2, 2, width - 2, height - 2, radius),
            smooth=True, fill=bg,
        )
        self._label = self.create_text(width / 2, height / 2, text=text,
                                        fill=fg, font=font)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")

    def _on_enter(self, _e):
        if self._enabled:
            self.itemconfig(self._rect, fill=self._bg_hover)

    def _on_leave(self, _e):
        if self._enabled:
            self.itemconfig(self._rect, fill=self._bg)

    def _on_click(self, _e):
        if self._enabled and self._cmd:
            self._cmd()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.itemconfig(self._rect, fill=self._bg if enabled else DISABLED_BG)
        self.itemconfig(self._label, fill=self._fg if enabled else DISABLED_FG)
        self.configure(cursor="hand2" if enabled else "arrow")

    def set_text(self, text: str):
        self.itemconfig(self._label, text=text)


class ProgressBar(tk.Canvas):
    """A themed rounded progress bar (0-100)."""

    def __init__(self, parent, width, height=8):
        super().__init__(parent, width=width, height=height, bg=BG,
                         highlightthickness=0, bd=0)
        # NB: do NOT use self._w / self._h here - _w is tkinter's internal
        # widget path name; clobbering it breaks every later canvas call.
        self._pw, self._ph = width, height
        r = height / 2
        self.create_polygon(_round_rect_points(0, 0, width, height, r),
                            smooth=True, fill=TROUGH)
        self._fill = self.create_polygon(
            _round_rect_points(0, 0, height, height, r),
            smooth=True, fill=BAR_FILL, state="hidden",
        )
        self._r = r

    def set(self, pct: float):
        pct = max(0.0, min(100.0, pct))
        if pct <= 0:
            self.itemconfig(self._fill, state="hidden")
            return
        w = max(self._ph, self._pw * pct / 100.0)
        self.itemconfig(self._fill, state="normal")
        self.coords(self._fill, *_round_rect_points(0, 0, w, self._ph, self._r))


class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Banjo-Tooie PC Launcher")
        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self._set_window_icon()

        self.config = load_config()
        self.package_path = tk.StringVar(value=self.config.get("package_path", ""))
        self.auto_play = tk.BooleanVar(value=bool(self.config.get("auto_play", False)))
        self.status_text = tk.StringVar(value="")

        self._build_ui()
        self._refresh_state()

    def _set_window_icon(self):
        """Set the titlebar/taskbar window icon (both OSes) from the bundled
        PNG. Kept as an attribute so tkinter doesn't garbage-collect it."""
        try:
            if os.path.exists(ICON_PNG):
                self._icon_img = tk.PhotoImage(file=ICON_PNG)
                self.root.iconphoto(True, self._icon_img)
        except Exception:  # noqa: BLE001 - a missing/odd icon must never crash the launcher
            pass

    # ---- UI construction -------------------------------------------------
    def _build_ui(self):
        self._build_header()

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=(16, 18))

        # Package selector - the field is editable so the path can also be
        # pasted/typed directly (the XBLA package has no extension, which some
        # file pickers hide; pasting the full path always works).
        tk.Label(body, text="YOUR XBLA PACKAGE   —   browse, or type/paste the full path",
                 bg=BG, fg=MUTED, font=(UI_FONT, 8, "bold")).pack(anchor="w")
        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=(4, 14))
        entry = tk.Entry(row, textvariable=self.package_path,
                         fg=TEXT, bg=ENTRY_BG, insertbackground=TEXT,
                         relief="flat", font=(UI_FONT, 10))
        entry.pack(side="left", fill="both", expand=True, ipady=6, padx=(0, 8))
        entry.bind("<FocusOut>", lambda e: self._commit_path())
        entry.bind("<Return>", lambda e: self._commit_path())
        RoundedButton(row, "Browse", self._browse_package, 96, 34,
                      bg=GOLD, bg_hover=GOLD_HI, fg=GOLD_TEXT,
                      font=(UI_FONT, 10, "bold")).pack(side="left")

        # Step 1 - extract
        self.extract_btn = RoundedButton(
            body, "Extract Game Data", self._extract_clicked, CONTENT_W, 40,
            bg=GOLD, bg_hover=GOLD_HI, fg=GOLD_TEXT)
        self.extract_btn.pack(fill="x")

        self.progress = ProgressBar(body, CONTENT_W, 8)
        self.progress.pack(fill="x", pady=(12, 6))

        self.status_label = tk.Label(body, textvariable=self.status_text, bg=BG,
                                     fg=MUTED, font=(UI_FONT, 9),
                                     anchor="w", justify="left", wraplength=CONTENT_W)
        self.status_label.pack(fill="x")

        tk.Frame(body, bg=SEP, height=1).pack(fill="x", pady=16)

        # Step 2 - play
        self.play_btn = RoundedButton(
            body, "▶  Play", self._play_clicked, CONTENT_W, 52,
            bg=GREEN, bg_hover=GREEN_HI, fg=GREEN_TXT,
            font=(UI_FONT, 14, "bold"))
        self.play_btn.pack(fill="x")

        tk.Checkbutton(
            body,
            text="  Skip this launcher next time (auto-play once extracted)",
            variable=self.auto_play, command=self._toggle_autoplay,
            bg=BG, fg=TEXT, activebackground=BG, activeforeground=TEXT,
            selectcolor=ENTRY_BG, font=(UI_FONT, 9), anchor="w",
            highlightthickness=0, bd=0, cursor="hand2",
        ).pack(anchor="w", fill="x", pady=(12, 0))

        tk.Label(
            body,
            text=("Game data, saves and config all live in the  BanjoTooie-Data/  folder\n"
                  "next to this launcher — delete it to start fresh."),
            bg=BG, fg=MUTED, font=(UI_FONT, 8), justify="left",
        ).pack(anchor="w", pady=(10, 0))

        self.exe_status = tk.Label(body, text="", bg=BG, fg=MUTED,
                                   font=(UI_FONT, 8), justify="left",
                                   wraplength=CONTENT_W, anchor="w")
        self.exe_status.pack(anchor="w", fill="x", pady=(6, 0))

    def _build_header(self):
        h = 96
        c = tk.Canvas(self.root, width=WIN_W, height=h, highlightthickness=0, bd=0)
        c.pack(fill="x")
        # vertical gold gradient
        r1, g1, b1 = self.root.winfo_rgb(GOLD_TOP)
        r2, g2, b2 = self.root.winfo_rgb(GOLD_BOT)
        for i in range(h):
            t = i / (h - 1)
            r = int((r1 + (r2 - r1) * t) / 256)
            g = int((g1 + (g2 - g1) * t) / 256)
            b = int((b1 + (b2 - b1) * t) / 256)
            c.create_line(0, i, WIN_W, i, fill=f"#{r:02x}{g:02x}{b:02x}")
        # decorative honeycomb on the right
        for cx, cy, s in ((498, 30, 20), (540, 58, 20), (498, 86, 20), (556, 20, 13)):
            self._hexagon(c, cx, cy, s, outline=HEX_LINE, width=2)
        c.create_text(26, 40, anchor="w", text="Banjo-Tooie",
                      fill=HEAD_TEXT, font=(UI_FONT, 26, "bold"))
        c.create_text(28, 70, anchor="w", text="PC  L A U N C H E R",
                      fill=HEAD_TEXT, font=(UI_FONT, 10, "bold"))

    @staticmethod
    def _hexagon(canvas, cx, cy, size, **kw):
        import math
        pts = []
        for k in range(6):
            ang = math.radians(60 * k - 30)
            pts += [cx + size * math.cos(ang), cy + size * math.sin(ang)]
        canvas.create_polygon(pts, fill="", **kw)

    # ---- state -----------------------------------------------------------
    def _refresh_state(self):
        exe = find_game_exe()
        if not exe:
            self.exe_status.config(
                text=f"⚠  {EXE_NAME} not found next to the launcher or in the "
                "build output — build it first (see README.md).",
                fg=ERR)
        else:
            self.exe_status.config(text=f"Using:  {exe}", fg=MUTED)

        extracted = _game_data_present()
        if os.path.exists(EXTRACT_MARKER) and not extracted:
            # The marker survived but the actual game data didn't (deleted or
            # moved after extracting) - clear the stale marker so state stays
            # honest rather than re-showing "ready to play" forever.
            try:
                os.remove(EXTRACT_MARKER)
            except OSError:
                pass
        has_package = bool(self.package_path.get()) and os.path.exists(self.package_path.get())

        self.extract_btn.set_enabled(has_package)
        self.play_btn.set_enabled(extracted and bool(exe))

        if extracted:
            self.status_text.set("✓  Game data extracted. Ready to play.")
        elif has_package:
            self.status_text.set("Package selected. Click “Extract Game Data” once before playing.")
        else:
            self.status_text.set("Select your XBLA package to get started.")

    def _browse_package(self):
        # The XBLA package has NO file extension. Use "*" (not "*.*") - on
        # GTK/Linux (the Steam Deck's picker) "*.*" only matches names with a
        # dot, which hides the extensionless package; "*" shows every file.
        path = filedialog.askopenfilename(
            title="Select your Banjo-Tooie XBLA package",
            filetypes=[("All files", "*")],
        )
        if not path:
            return
        self.package_path.set(path)
        self.config["package_path"] = path
        save_config(self.config)
        self._refresh_state()

    def _commit_path(self):
        """Save the path currently typed/pasted into the entry field."""
        path = self.package_path.get().strip().strip('"').strip("'")
        if path != self.package_path.get():
            self.package_path.set(path)
        if path != self.config.get("package_path"):
            self.config["package_path"] = path
            save_config(self.config)
        self._refresh_state()

    def _toggle_autoplay(self):
        self.config["auto_play"] = bool(self.auto_play.get())
        save_config(self.config)

    def _extract_clicked(self):
        path = self.package_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Select a valid package file first.")
            return
        self.extract_btn.set_enabled(False)
        self.play_btn.set_enabled(False)
        threading.Thread(target=self._extract_worker, args=(path,), daemon=True).start()

    def _extract_worker(self, path: str):
        try:
            self._set_status("Reading package...")
            pkg = StfsPackage(path)

            def progress(done, total, name):
                pct = (done / total * 100) if total else 0
                self._set_status(f"Extracting {name} ({done}/{total})...")
                self._set_progress(pct)

            extracted = pkg.extract_all(GAME_DATA_DIR, progress=progress)

            self._set_status("Verifying game version...")
            xex_path = os.path.join(GAME_DATA_DIR, "default.xex")
            if not os.path.isfile(xex_path):
                raise RuntimeError(
                    "default.xex wasn't found in the extracted package - is this "
                    "really a Banjo-Tooie XBLA package?")
            actual_hash = _hash_file(xex_path)
            if actual_hash != TESTED_XEX_SHA256:
                # Don't leave a half-verified game_data/ sitting around looking
                # like it's ready to play - remove it so the next attempt (or a
                # confused bug report) starts from a clean, honest state.
                shutil.rmtree(GAME_DATA_DIR, ignore_errors=True)
                raise RuntimeError(
                    "This package's default.xex doesn't match the exact XBLA "
                    "version this launcher was built and tested against "
                    f"(got {actual_hash[:12]}..., expected "
                    f"{TESTED_XEX_SHA256[:12]}...). It may be a different "
                    "region/revision or a corrupted file - the game likely "
                    "wouldn't run correctly, so nothing was kept.")

            with open(EXTRACT_MARKER, "w", encoding="utf-8") as f:
                f.write(f"{len(extracted)} files extracted from {os.path.basename(path)}\n")
                f.write(f"default.xex sha256: {actual_hash}\n")
            self._set_status(f"Extracted {len(extracted)} files successfully.")
        except Exception as e:  # noqa: BLE001 - surface any failure to the user
            self._set_status(f"Extraction failed: {e}")
            self.root.after(0, lambda: messagebox.showerror("Extraction failed", str(e)))
        finally:
            self.root.after(0, self._refresh_state)

    def _set_status(self, text: str):
        self.root.after(0, lambda: self.status_text.set(text))

    def _set_progress(self, pct: float):
        self.root.after(0, lambda: self.progress.set(pct))

    def _launch_game(self) -> bool:
        """Start the game as an independent process. Returns True on success."""
        # Re-check right before launching, not just when the UI last refreshed
        # - the Play button being enabled reflects state as of the last
        # refresh, and game_data/ could have been deleted or moved in the
        # meantime (e.g. the player freed disk space) without the launcher
        # knowing yet. Better a clear message here than the game crashing
        # partway through boot with no game data to load.
        if not _game_data_present():
            messagebox.showerror(
                "Game data missing",
                "The extracted game data is missing or incomplete (was "
                "BanjoTooie-Data\\game_data deleted or moved?). Click "
                "“Extract Game Data” again before playing.")
            self._refresh_state()
            return False
        exe = find_game_exe()
        if not exe:
            messagebox.showerror("Error", f"{EXE_NAME} not found.")
            return False
        os.makedirs(SAVES_DIR, exist_ok=True)

        env = os.environ.copy()
        env["REX_MNK_MODE"] = "true"
        env["REX_KEYBIND_START"] = "Return"
        env["REX_USER_DATA_ROOT"] = SAVES_DIR

        exe_dir = os.path.dirname(exe)
        if not IS_WINDOWS:
            # On Linux the game finds its shared objects (librexruntime*.so,
            # libTracyClient*.so) via LD_LIBRARY_PATH; they sit next to the
            # binary. On Windows the DLLs are found from the exe's own dir.
            ld = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = exe_dir + (os.pathsep + ld if ld else "")
            # Suppress the RenderDoc Vulkan capture overlay ("Capturing Vulkan…
            # F12 to capture"). The game only *detects* RenderDoc, never requests
            # it - so if the overlay shows, RenderDoc's capture layer is being
            # pulled in by the environment (an implicit layer, or an inherited
            # ENABLE_VULKAN_RENDERDOC_CAPTURE). Tell the Vulkan loader to disable
            # that layer, and drop the enable-var (RenderDoc treats it as "on"
            # whenever it's merely present, regardless of value).
            env.pop("ENABLE_VULKAN_RENDERDOC_CAPTURE", None)
            disabled = env.get("VK_LOADER_LAYERS_DISABLE", "")
            env["VK_LOADER_LAYERS_DISABLE"] = (
                (disabled + ",") if disabled else "") + "VK_LAYER_RENDERDOC_Capture"

        argv = [exe, "--game_data_root", GAME_DATA_DIR]

        if not IS_WINDOWS:
            # Steam Deck Gaming Mode: gamescope binds the Steam session to the
            # process it launched (this launcher) and to the first top-level
            # surface that process shows. If we Popen a *separate* game process
            # and then exit, gamescope tears down the tracked PID/surface (the
            # launcher window) and never adopts the detached game window -> black
            # screen + no sound. Instead we replace THIS process image with the
            # game via execve, so the game keeps the exact PID gamescope tracks
            # and its window is the tracked process's surface. Tear down the
            # launcher's own Tk surface first so it doesn't linger as the bound
            # window. execve does not return on success. (PyInstaller onefile:
            # this runs in the bootloader's child; execve replaces the child, the
            # parent keeps waiting and cleans up _MEIPASS when the game exits.)
            try:
                os.chdir(exe_dir)
                self.root.destroy()
                os.execve(exe, argv, env)
            except OSError as e:
                messagebox.showerror("Failed to launch", str(e))
                return False
            return True  # unreachable on success (execve replaced the process)

        try:
            subprocess.Popen(argv, cwd=exe_dir, env=env)
        except OSError as e:
            messagebox.showerror("Failed to launch", str(e))
            return False
        return True

    def _play_clicked(self):
        # On Linux _launch_game() execve's into the game and never returns; on
        # Windows the game runs independently (its binary + data live in
        # persistent folders next to the launcher, not the frozen temp dir), so
        # close the launcher on success - the player asked not to leave it
        # hanging.
        if self._launch_game():
            self.root.destroy()

    def maybe_autoplay(self) -> bool:
        """If auto-play is enabled and the game is ready, launch it straight
        away and skip showing the launcher window. Returns True if it launched.
        Turn auto-play off again via the checkbox, or by editing
        BanjoTooie-Data/launcher_config.xml (<auto_play>false</auto_play>).
        On Linux this execve's into the game (see _launch_game) and never
        returns."""
        if not self.auto_play.get():
            return False
        if not _game_data_present() or not find_game_exe():
            return False
        if self._launch_game():
            self.root.destroy()
            return True
        return False


def _center(root: tk.Tk):
    root.update_idletasks()
    x = (root.winfo_screenwidth() - WIN_W) // 2
    y = (root.winfo_screenheight() - WIN_H) // 3
    root.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")


def main():
    root = tk.Tk()
    root.withdraw()   # stay hidden until we know whether we're auto-playing
    err = provision_game()
    if err:
        messagebox.showwarning("Setup", err)
    app = LauncherApp(root)
    if app.maybe_autoplay():
        # Launched straight into the game; the window was never shown and the
        # root is already destroyed - nothing left to loop over.
        return
    _center(root)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
