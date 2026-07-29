#!/usr/bin/env bash
export DISPLAY=:0
pkill -f "bt_linux_test/Banjo-Tooie" 2>/dev/null || true
sleep 1
cd "$HOME/bt_linux_test"
setsid ./Banjo-Tooie >/tmp/bt_cap.out 2>&1 < /dev/null &
sleep 6
# window id is the first field of the xwininfo tree line for our title
WID=$(xwininfo -root -tree 2>/dev/null | grep "Banjo-Tooie PC Launcher" | head -1 | awk '{print $1}')
echo "window id: $WID"
if [ -n "$WID" ]; then
  import -window "$WID" /mnt/d/Temp/tooie/steamdeck/launcher_linux.png && echo "captured"
  ls -la /mnt/d/Temp/tooie/steamdeck/launcher_linux.png
else
  echo "no launcher window found"
fi
