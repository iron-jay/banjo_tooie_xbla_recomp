# Banjo-Tooie PC Launcher

A small GUI that takes your own legally-owned Banjo-Tooie XBLA package and
gets you into the game: extracts the game data, then launches the
recompiled `banjotooie.exe`.

**This does not compile anything.** The recompiled executable is the same
for every player (it's derived from Microsoft/Rare's published XBLA
binary, which doesn't vary between legitimate copies) - the only thing that
differs per player is their own game data, which is what gets extracted
here. This mirrors how other "recomp" launchers (Zelda64Recomp etc.) work.

---

## For players (the single-file release)

The release is **one file** - `Banjo-Tooie.exe` on Windows, `Banjo-Tooie` on
Linux. Nothing to install: no Python, no Visual C++ redistributable (Windows),
and the game binaries + their runtime libraries are bundled inside it.

1. Download the file for your OS and put it in its own folder somewhere you can
   write to (e.g. a new folder in Documents/Desktop, or `~/Games/BanjoTooie` -
   **not** Program Files or another read-only location).
2. Run it:
   - **Windows**: double-click. SmartScreen may warn about an unknown publisher
     (expected for an unsigned indie exe) - click *More info -> Run anyway*.
   - **Linux / Steam Deck**: `chmod +x Banjo-Tooie` then run it (or from Steam
     Deck desktop mode, mark it executable in Dolphin -> Properties, then
     double-click). To use it in Game Mode, add it as a Non-Steam Game.
3. Click **Browse** and select your own Banjo-Tooie XBLA package - the STFS
   container you copied off your own Xbox 360 profile (it starts with the
   bytes `LIVE`). The package has **no file extension**; if a picker hides it,
   just **type or paste the file's full path** into the field instead (it's
   editable) and press Enter.
4. Click **Extract Game Data** (one-time per package; it remembers your
   package and skips re-extracting next time). The launcher checks the
   extracted `default.xex` against the exact XBLA build this port was tested
   against and refuses a mismatch (wrong region/revision, or a corrupted
   file) rather than extracting data the game likely can't run correctly.
5. Click **Play**. If `game_data/` has gone missing or incomplete since you
   extracted (e.g. it got deleted to free up space), the launcher catches
   that here instead of letting the game crash, and asks you to extract again.

**Auto-play:** tick *"Skip this launcher next time (auto-play once extracted)"*
and, once your data is extracted, future runs launch the game straight away
without showing the launcher. To turn it back off, either untick it (it shows
the launcher again the next time it *doesn't* auto-play) or edit
`BanjoTooie-Data/launcher_config.xml` and set `<auto_play>false</auto_play>`.

Everything the launcher creates lives in **one folder next to the launcher**,
`BanjoTooie-Data/`, so the game is fully portable - move or delete that folder
and nothing is left behind elsewhere. Inside it:

- `game/` - the game binaries, unpacked out of the launcher on first run.
- `game_data/` - your extracted game files (safe to delete and re-extract).
- `saves/` - save games + shader cache (**not** your Documents folder).
  Zip `BanjoTooie-Data/` up to hand off a crash repro - it's self-contained.
- `launcher_config.xml` - remembers your package path and the auto-play setting.

Controls default to keyboard/mouse; a plugged-in Xbox controller also works
(the Steam Deck's built-in controls count). Default Start button is **Enter**.

---

## For developers (building the release)

`build_release.py` is cross-platform - run it with the target OS's Python and it
produces that OS's single-file artifact. It stages the game binaries into
`_payload/`, then runs PyInstaller `--onefile --windowed` with that payload
embedded.

**Windows** (produces `dist\Banjo-Tooie.exe`):
- Python 3.10+ and `pip install pyinstaller`
- A built **Release** `banjotooie.exe` + `rexruntime.dll` (see `../CLAUDE.md`
  -> "Build")
- Bundles the four MSVC runtime DLLs the game imports (`MSVCP140`,
  `MSVCP140_ATOMIC_WAIT`, `VCRUNTIME140`, `VCRUNTIME140_1`, copied from
  `%WINDIR%\System32`) - the only deps beyond what Windows 10/11 ships. The
  `api-ms-win-crt-*` imports are the Universal CRT and are already part of
  Windows, so they are not bundled.

```
python build_release.py
```

**Linux / Steam Deck** (produces `dist/Banjo-Tooie`):
- Python 3.10+, `python3-tk`, and `pip install pyinstaller`
- A built Linux `banjotooie` + `librexruntime[d].so` (see `../CLAUDE.md`
  -> "Steam Deck"). GTK3 / the Vulkan loader / X11 / Wayland are system
  libraries present on any desktop Linux incl. SteamOS, so they are not bundled.

```
python build_release.py <path-to-linux-build-dir>   # e.g. .../linux-amd64-release
```

**Linux glibc caveat:** a PyInstaller binary (and the game binary itself)
requires a glibc **at least as new as the build box's**. Build the Linux release
on the *oldest* glibc you need to support (an older Ubuntu, or a manylinux
container) if it must run on the current Steam Deck, whose SteamOS ships an
older glibc than bleeding-edge distros.

Point either build at a specific build dir by passing it as the first argument.

### Running from source (no packaging)

`python launcher.py` (Python 3.10+, stdlib only - `tkinter`; Linux needs the
`python3-tk` system package). When not frozen it finds the game binary in the
dev build tree (`../banjotooie-recomp/out/build/<platform>-release`, then
`-debug`) instead of a bundled copy, and keeps the `BanjoTooie-Data/` folder
(game_data / saves / `launcher_config.xml`) next to `launcher.py`.

## Files

- `Banjo-Tooie.exe` / `Banjo-Tooie` (`dist/`) - the packaged single-file
  releases (Windows / Linux).
- `build_release.py` - cross-platform; stages the payload and drives PyInstaller
  (embeds `banjotooie.ico` in the Windows exe, bundles `banjotooie.png` for the
  window icon on both OSes).
- `launcher.py` - the GUI (tkinter), cross-platform and frozen-aware: keeps
  player data next to the launcher and self-provisions the bundled game
  binaries into `game/` (with the exec bit restored on Linux).
- `make_icon.py` - regenerates the icon art (`banjotooie.png` / `.ico`); needs
  `pip install pillow`. Original honeycomb design, not the game's tile art.
- `banjotooie.png` / `banjotooie.ico` - the app/window icon (checked in; only
  re-run `make_icon.py` to change the art).
- `stfs_extract.py` - the STFS package reader. Byte offsets for the file
  table were reverse-engineered and validated against a known-good prior
  extraction (all 35+ real files matched byte-for-byte). No signature
  verification, no directory nesting - this package doesn't use either.
