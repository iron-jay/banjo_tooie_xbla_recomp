# Next session: fix the Steam Deck Gaming Mode launcher → black screen

Paste the block below to start the next session. Read `D:\Temp\tooie\CLAUDE.md` first
(esp. the "Known issue: Gaming Mode launcher → game BLACK SCREEN" subsection under the
Steam Deck section).

---

## Prompt

Continuing the Banjo-Tooie → PC port. Read CLAUDE.md first. One focused task this session:

**Fix the Steam Deck Gaming Mode black screen.** On the user's real Steam Deck, in **Gaming Mode**,
opening the Non-Steam launcher and hitting **Play** gives a **black screen + no sound** — the game
process runs, but its window/audio never becomes the foreground gamescope surface. It already WORKS
(a) when the launcher's **auto-play** checkbox is ticked (launcher never shows its own window), and
(b) in **Desktop Mode**. Make the normal launcher→Play flow work in Gaming Mode too.

### Where the code is
`D:\Temp\tooie\launcher\launcher.py`:
- `_launch_game()` — sets env (`REX_MNK_MODE`, `REX_KEYBIND_START`, `REX_USER_DATA_ROOT`,
  `LD_LIBRARY_PATH`, RenderDoc-layer suppression) and does `subprocess.Popen([exe, "--game_data_root",
  GAME_DATA_DIR], cwd=exe_dir, env=env)`, returns True.
- `_play_clicked()` — calls `_launch_game()` then `self.root.destroy()` (closes the launcher).
- `maybe_autoplay()` — the auto-play path; same `_launch_game()` + `destroy()`, but the window was
  `withdraw()`n in `main()` and never shown.

### Leading hypothesis
gamescope binds the Steam game session to the FIRST top-level window / the tracked process. Manual
Play shows the LAUNCHER window first (gamescope binds to it), then the launcher exits → the bound
surface/PID is torn down and the separately-spawned (detached) game window is never adopted → black.
Auto-play works because no launcher window is ever shown, so the GAME window is the first surface.

### Fix to try FIRST
On **Linux only**, replace the launcher process image with the game via `os.execve(exe, [exe,
"--game_data_root", GAME_DATA_DIR], env)` (after `os.chdir(exe_dir)`) instead of `Popen`+`destroy()`,
so the game inherits the Steam-tracked process slot/PID. Notes:
- `os.execve` does not return on success, so restructure `_launch_game()`/`_play_clicked()`/
  `maybe_autoplay()` accordingly (the Windows path must stay `Popen`+`destroy()` — it works there).
- The launcher is a **PyInstaller onefile**: the Python code runs in the bootloader's child. `execve`
  in that child replaces it with the game; the bootloader parent stays and waits, and `_MEIPASS` is
  cleaned when the game exits — so the game ends up as the tracked child in Steam's process tree.
- Keep all the env setup (LD_LIBRARY_PATH, RenderDoc suppression, REX_* vars) before the exec.

### Fallbacks if exec isn't enough
- `self.root.withdraw()` (hide launcher window) then `subprocess.run([...])` (block/stay alive as the
  parent) instead of exiting — keeps the tracked PID alive and removes the launcher surface.
- gamescope/Steam window hints or env cues (e.g. detect `SteamDeck`/`STEAM_COMPAT_*`/gamescope and
  behave differently); investigate what Steam expects of a Non-Steam "game" that spawns a child.

### Iteration is FAST (launcher-only)
This is a `launcher.py`-only change — **no game rebuild needed**. After editing, repackage the
launchers (SEQUENTIALLY, never concurrently — they share `_payload/`/`build/`/`dist/`):
- Linux (the one the Deck needs): `wsl -d Ubuntu-24.04 -u root -- bash -c "sed 's/\r$//'
  /mnt/d/Temp/tooie/steamdeck/build_launcher_2404.sh | bash"` → `launcher/dist/Banjo-Tooie`.
- Windows: `cd D:\Temp\tooie\launcher; python build_release.py`.

### Testing
**Cannot be reproduced in WSL — there is no gamescope there.** The user must test each candidate build
on the actual Deck in Gaming Mode. So: make the most-likely-correct single change (execve), hand the
user the rebuilt `dist/Banjo-Tooie`, and have them report black-screen-or-works; iterate from there.
Ask the user to test rather than claiming it's fixed.
