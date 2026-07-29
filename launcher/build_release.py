"""Build a single self-contained Banjo-Tooie launcher for a GitHub release.

Cross-platform: run it with the platform's Python and it produces the right
single-file artifact for that OS.

  Windows ->  dist\\Banjo-Tooie.exe   (no Python, no VC++ redist needed)
  Linux   ->  dist/Banjo-Tooie       (no Python needed; see glibc note below)

The game binaries are bundled inside the launcher; on first run the launcher
unpacks them into a  game/  folder next to itself (see provision_game() in
launcher.py). The player supplies only their own XBLA package.

  - Windows payload: banjotooie.exe + rexruntime.dll  (from the build dir)
    plus the 4 MSVC runtime DLLs from %WINDIR%\\System32.
  - Linux payload:   banjotooie (from the build dir) + librexruntime[d].so
    [+ libTracyClient[d].so if the build has Tracy on] from the SDK out dir
    (rexglue-sdk/out/linux-amd64). GTK3 / Vulkan loader / X11 / Wayland are
    system libraries present on any desktop Linux incl. SteamOS, so they are
    NOT bundled.

Usage:
    python build_release.py                # default: the platform's Release dir
    python build_release.py <build_dir>    # point at a specific build output

Requirements on the BUILD machine (not the player's):
    - Python 3.10+  and  pip install pyinstaller  (Linux also needs python3-tk)
    - A built banjotooie for the target OS (see ../CLAUDE.md "Build" / Steam Deck)

Linux glibc note: a PyInstaller/onefile binary (and the game binary itself)
requires a glibc at least as new as the BUILD box's. Build the Linux release on
the OLDEST glibc you want to support (e.g. an older Ubuntu / a manylinux
container) if you need it to run on the current Steam Deck, whose SteamOS ships
an older glibc than bleeding-edge distros.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys

IS_WINDOWS = os.name == "nt"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))

PAYLOAD_STAGE = os.path.join(HERE, "_payload")
DIST_DIR = os.path.join(HERE, "dist")
APP_NAME = "Banjo-Tooie"
OUT_NAME = APP_NAME + (".exe" if IS_WINDOWS else "")

_PLATFORM = "win-amd64" if IS_WINDOWS else "linux-amd64"
DEFAULT_BUILD_DIR = os.path.join(
    REPO, "banjotooie-recomp", "out", "build", f"{_PLATFORM}-release")

# The exact DLLs the game imports beyond what Windows 10/11 ships with. The
# api-ms-win-crt-* imports are the Universal CRT and are part of Windows; only
# these four (the VC++ 2015-2022 redistributable) can be missing on a clean PC.
VC_RUNTIME_DLLS = [
    "MSVCP140.dll",
    "MSVCP140_ATOMIC_WAIT.dll",
    "VCRUNTIME140.dll",
    "VCRUNTIME140_1.dll",
]


def die(msg: str) -> "None":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _copy(src: str, label: str) -> None:
    # shutil.copy (not copy2) - copies data + mode but skips the timestamp
    # copystat/utime step, which fails intermittently on the WSL drvfs mount.
    shutil.copy(src, os.path.join(PAYLOAD_STAGE, os.path.basename(src)))
    print(f"  + {os.path.basename(src)}  ({os.path.getsize(src) // 1024} KB) {label}")


def stage_payload(build_dir: str) -> None:
    """Collect the game binaries (+ platform runtime libs) into _payload/."""
    if os.path.isdir(PAYLOAD_STAGE):
        shutil.rmtree(PAYLOAD_STAGE)
    os.makedirs(PAYLOAD_STAGE)

    if IS_WINDOWS:
        for name in ("banjotooie.exe", "rexruntime.dll"):
            src = os.path.join(build_dir, name)
            if not os.path.exists(src):
                die(f"{name} not found in {build_dir}\n"
                    f"       Build the Release target first (see ../CLAUDE.md).")
            _copy(src, "")
        sys32 = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32")
        for name in VC_RUNTIME_DLLS:
            src = os.path.join(sys32, name)
            if not os.path.exists(src):
                die(f"VC runtime DLL {name} not found in {sys32}. Install the "
                    f"Visual C++ 2015-2022 x64 redistributable on this build box.")
            _copy(src, "(VC++ runtime)")
        return

    # Linux: binary from the build dir, .so libs from the SDK out dir.
    binary = os.path.join(build_dir, "banjotooie")
    if not os.path.exists(binary):
        die(f"banjotooie not found in {build_dir}\n"
            f"       Build the Linux target first (see ../CLAUDE.md 'Steam Deck').")
    _copy(binary, "")

    sfx = "d" if os.path.basename(build_dir.rstrip("/")).endswith("debug") else ""
    so_dir = os.path.join(REPO, "rexglue-sdk", "out", "linux-amd64")
    rex_so = os.path.join(so_dir, f"librexruntime{sfx}.so")
    if not os.path.exists(rex_so):
        die(f"{os.path.basename(rex_so)} not found in {so_dir}. Build the matching "
            f"Linux config first.")
    _copy(rex_so, "(runtime)")
    # Tracy is only linked in when Perf Counters / Tracy are on (Debug); a
    # Release build won't have it and won't need it.
    tracy_so = os.path.join(so_dir, f"libTracyClient{sfx}.so")
    if os.path.exists(tracy_so):
        _copy(tracy_so, "(Tracy - debug builds only)")


def write_payload_stamp() -> None:
    """Write payload_version.txt: a sha256 over the staged files (names +
    contents). The launcher compares its bundled stamp against the one it
    copied into game/ at provision time, so a launcher carrying updated game
    binaries re-provisions an existing install instead of silently keeping
    the old ones."""
    h = hashlib.sha256()
    for name in sorted(os.listdir(PAYLOAD_STAGE)):
        h.update(name.encode("utf-8"))
        with open(os.path.join(PAYLOAD_STAGE, name), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    stamp = h.hexdigest()
    with open(os.path.join(PAYLOAD_STAGE, "payload_version.txt"), "w") as f:
        f.write(stamp + "\n")
    print(f"  + payload_version.txt  ({stamp[:16]}...)")


def run_pyinstaller() -> None:
    # Clean the work dir, but only remove THIS platform's own prior artifact
    # from dist/ - so the Windows .exe and the Linux binary can coexist there.
    work = os.path.join(HERE, "build")
    if os.path.isdir(work):
        shutil.rmtree(work)
    prior = os.path.join(DIST_DIR, OUT_NAME)
    if os.path.exists(prior):
        os.remove(prior)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile",
        "--windowed",                       # GUI app - no console/terminal window
        "--name", APP_NAME,
        "--distpath", DIST_DIR,
        "--workpath", os.path.join(HERE, "build"),
        "--specpath", HERE,
        "--add-data", f"{PAYLOAD_STAGE}{os.pathsep}payload",
        os.path.join(HERE, "launcher.py"),
    ]
    icon_png = os.path.join(HERE, "banjotooie.png")
    if os.path.exists(icon_png):
        # Bundle the PNG so the tkinter window icon works on both OSes.
        cmd[len(cmd) - 1:len(cmd) - 1] = ["--add-data", f"{icon_png}{os.pathsep}."]
    icon_ico = os.path.join(HERE, "banjotooie.ico")
    if IS_WINDOWS and os.path.exists(icon_ico):
        # Embed the multi-size icon into the .exe itself (Windows only; a Linux
        # ELF can't carry an icon - use the .desktop/Steam entry + window icon).
        cmd[cmd.index("--windowed") + 1:cmd.index("--windowed") + 1] = ["--icon", icon_ico]
    print("\nRunning PyInstaller:\n  " + " ".join(cmd) + "\n")
    subprocess.run(cmd, check=True, cwd=HERE)


def main() -> None:
    build_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUILD_DIR
    print(f"Build dir: {build_dir}   (OS: {'Windows' if IS_WINDOWS else 'Linux'})")
    if not os.path.isdir(build_dir):
        die(f"build dir does not exist: {build_dir}\n"
            f"       Pass the correct build output dir as the first argument.")

    print("\nStaging payload:")
    stage_payload(build_dir)
    write_payload_stamp()

    run_pyinstaller()

    out = os.path.join(DIST_DIR, OUT_NAME)
    if not os.path.exists(out):
        die("PyInstaller finished but the artifact was not produced.")
    size_mb = os.path.getsize(out) / (1024 * 1024)
    print(f"\nDone.\n  {out}\n  {size_mb:.1f} MB - this single file is the release artifact.")
    shutil.rmtree(PAYLOAD_STAGE, ignore_errors=True)


if __name__ == "__main__":
    main()
