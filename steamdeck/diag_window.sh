#!/usr/bin/env bash
export DISPLAY=:0
pkill -f "bt_linux_test/Banjo-Tooie" 2>/dev/null || true
sleep 1
TEST="$HOME/bt_linux_test"
cd "$TEST"
setsid ./Banjo-Tooie >/tmp/bt_launcher2.out 2>&1 < /dev/null &
sleep 5
echo "=== process ==="
pgrep -af "bt_linux_test/Banjo-Tooie" | grep -v pgrep || echo "not running"
echo "=== stderr/stdout ==="
cat /tmp/bt_launcher2.out | head -20
echo "=== X windows (xwininfo -root -tree), banjo/tk matches ==="
xwininfo -root -tree 2>/dev/null | grep -iE "banjo|tooie|tk|launcher" || echo "no matching X window"
echo "=== all top-level X windows (first 15) ==="
xwininfo -root -tree 2>/dev/null | grep -E '^\s+0x' | head -15
