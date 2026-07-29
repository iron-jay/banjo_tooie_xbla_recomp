#!/usr/bin/env bash
BUILD=/mnt/d/Temp/tooie/banjotooie-recomp/out/build/linux-amd64-debug
SO=/mnt/d/Temp/tooie/rexglue-sdk/out/linux-amd64
echo "=== game binary + runtime .so present ==="
ls -la "$BUILD/banjotooie" "$SO"/*.so 2>/dev/null
echo
echo "=== ldd banjotooie (non-system deps of interest) ==="
LD_LIBRARY_PATH="$SO" ldd "$BUILD/banjotooie" 2>&1 | grep -iE "rexruntime|tracy|SDL|vulkan|gtk|not found" || echo "(only base system libs)"
echo
echo "=== ldd librexruntimed.so (what IT pulls in) ==="
LD_LIBRARY_PATH="$SO" ldd "$SO/librexruntimed.so" 2>&1 | grep -iE "SDL|vulkan|gtk|wayland|X11|xcb|pulse|asound|not found" | sort -u || echo "(none flagged)"
echo
echo "=== WSL python: tkinter + pip + pyinstaller ==="
python3 -c "import tkinter; print('tkinter OK', tkinter.TkVersion)" 2>&1 | head -1
python3 -c "import PyInstaller; print('pyinstaller', PyInstaller.__version__)" 2>&1 | head -1
which pip3 pip 2>/dev/null || echo "no pip"
echo "=== glibc version on this build box (portability ceiling) ==="
ldd --version | head -1
