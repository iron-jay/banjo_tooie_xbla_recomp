# Banjo-Tooie (XBLA) → PC / Steam Deck

A native port of **Banjo-Tooie**, using the Xbox 360 XBLA re-release as the source, built by
statically recompiling its guest PowerPC code to C++ against **[ReXGlue](https://github.com/rexglue/rexglue-sdk)**
(a Xenia-derived Xbox 360 static-recompilation SDK). The result is a real Windows/Linux executable —
no emulator running at runtime, and no N64 ROM involved anywhere in the pipeline.

## Status

Playable end to end. Boots from the title screen through the main menu, save select, the full intro
cutscene, and into free-roaming, player-controlled gameplay — confirmed on both **Windows** (NVIDIA
GPU) and a **real Steam Deck** (RADV hardware Vulkan, including Steam's Gaming Mode). Controller,
keyboard/mouse, save/load, and the Windows/Linux launcher have all been used successfully by an
actual player, not just booted for a smoke test.

Known rough edges: a handful of the game's ~22,000 recompiled functions were missed by the initial
static analysis (the fix is always the same pattern — see the crash write-ups in the SDK submodule's
commit history if you hit one), full-game longevity beyond the opening areas is still lightly tested,
and audio output quality has not been verified by ear.

## You need your own copy of the game

**This repository does not, and will not, include any of Banjo-Tooie's game data.** No textures, no
audio, no strings, no executable — none of it. To play, you supply your own legally-owned XBLA
package (the `.xex`-containing STFS container you extract from your own Xbox 360 profile) and the
launcher pulls the game data out of *that*. This mirrors how other static-recompilation ports (e.g.
Zelda64Recomp) work: the tooling here is original, the game itself is not redistributed.

## For players

Grab the single-file launcher for your OS (`Banjo-Tooie.exe` / `Banjo-Tooie`) and point it at your
own XBLA package. Full instructions: **[launcher/README.md](launcher/README.md)**.

## Repository layout

| Path | What |
|---|---|
| `banjotooie-recomp/` | The recompiler's manifest (`banjotooie_manifest.toml`), function/switch-table overrides (`overrides.toml`), and the small host harness (CMake project) the recompiled code links into. |
| `rexglue-sdk/` | Git submodule — a fork of [rexglue/rexglue-sdk](https://github.com/rexglue/rexglue-sdk) with the bring-up fixes this port needed (audio-device fallback, keyboard/mouse input, a few kernel shims, a Linux window icon). |
| `launcher/` | The cross-platform (Windows/Linux) launcher: extracts a player's own XBLA package and runs the recompiled binary. See its own README. |
| `steamdeck/` | Scripts used to cross-build a glibc-portable Linux release targeting the Steam Deck from WSL. |

Not checked in (see `.gitignore`): the game's own data files, `banjotooie-recomp/generated/` (the
~3.4M lines of recompiled guest code — regenerable in about a minute via `rexglue codegen` against
your own copy of the game's executable, so it's treated as a build artifact rather than source), and
all build output.

## Building from source

Requires CMake ≥ 3.25, Clang ≥ 20, and Ninja (Windows also needs the VS Build Tools' MSVC/Windows
SDK; Linux additionally needs GTK3 + a Vulkan loader). With the toolchain in place:

```powershell
git clone --recurse-submodules <this-repo-url>
cd banjo_tooie_xbla_recomp
. .\rexenv.ps1   # puts clang/cmake/ninja on PATH (Windows)
cd banjotooie-recomp
cmake --preset win-amd64-release -DREXSDK_DIR=../rexglue-sdk `
  "-DCMAKE_C_FLAGS=-march=x86-64-v3" "-DCMAKE_CXX_FLAGS=-march=x86-64-v3"
cmake --build --preset win-amd64-release --target banjotooie
```

This produces `banjotooie.exe` (+ `rexruntime.dll`), but **it has no game data compiled in** — it
still needs `--game_data_root <path-to-your-extracted-xbla-files>` at launch, which is exactly what
the launcher automates. For the Linux/Steam Deck cross-build path, see the scripts under
`steamdeck/`.

## Credits

Built on [ReXGlue](https://github.com/rexglue/rexglue-sdk) by Tom Clay, itself derived from the
[Xenia](https://xenia.jp) project. Banjo-Tooie is the property of Microsoft/Rare; nothing in this
repository transfers any rights to their work.
