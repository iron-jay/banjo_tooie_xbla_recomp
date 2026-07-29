#!/usr/bin/env bash
export DISPLAY=:0
BUILD=/mnt/d/Temp/decomp/banjotooie-recomp/out/build/linux-amd64-release
export LD_LIBRARY_PATH=/mnt/d/Temp/decomp/rexglue-sdk/out/linux-amd64
export REX_USER_DATA_ROOT="$HOME/bt_verify"; mkdir -p "$REX_USER_DATA_ROOT"
cd "$BUILD"
setsid ./banjotooie --game_data_root /mnt/d/Temp/decomp/xbla/files >/tmp/gv.out 2>&1 </dev/null &
GP=$!
sleep 14
echo "=== game window (title should be 'Banjo-Tooie') ==="
LINE=$(xwininfo -root -tree 2>/dev/null | grep '"Banjo-Tooie"' | head -1)
echo "$LINE"
WID=$(echo "$LINE" | awk '{print $1}')
echo "=== _NET_WM_ICON on the window (present = window icon was set) ==="
if [ -n "$WID" ]; then
  xprop -id "$WID" _NET_WM_ICON 2>/dev/null | head -1 || echo "(no _NET_WM_ICON)"
else
  echo "(game window not found - checking log)"; tail -4 /tmp/gv.out
fi
kill -9 $GP 2>/dev/null; pkill -9 -f "linux-amd64-release/banjotooie" 2>/dev/null
rm -rf "$HOME/bt_verify"
