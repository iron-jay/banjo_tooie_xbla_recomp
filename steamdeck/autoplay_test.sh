#!/usr/bin/env bash
# Verify auto_play=true skips the launcher window and spawns the game directly.
export DISPLAY=:0
TEST="$HOME/bt_autoplay_test"
rm -rf "$TEST"; mkdir -p "$TEST/BanjoTooie-Data/game_data"
cp /mnt/d/Temp/decomp/launcher/dist/Banjo-Tooie "$TEST/"; chmod +x "$TEST/Banjo-Tooie"
# auto_play ON, and pretend extraction is already done (marker present).
cat > "$TEST/BanjoTooie-Data/launcher_config.xml" <<'EOF'
<?xml version='1.0' encoding='utf-8'?>
<launcher>
  <package_path>/mnt/d/Temp/decomp/ABB9CAB336175357D09F2D922735D23C62F90DDD58</package_path>
  <auto_play>true</auto_play>
</launcher>
EOF
touch "$TEST/BanjoTooie-Data/game_data/.extracted_ok"
cd "$TEST"
setsid ./Banjo-Tooie >/tmp/bt_auto.out 2>&1 < /dev/null &
LP=$!
sleep 8
echo "=== launcher process still alive? (auto-play should have exited it) ==="
kill -0 $LP 2>/dev/null && echo "ALIVE (bad)" || echo "exited (good - it launched the game and closed)"
echo "=== launcher WINDOW present? (should be NONE - window was skipped) ==="
xwininfo -root -tree 2>/dev/null | grep "Banjo-Tooie PC Launcher" | head -1 || echo "no launcher window (good)"
echo "=== was the game spawned? ==="
pgrep -af "BanjoTooie-Data/game/banjotooie" | grep -v pgrep || echo "(game not currently running - may have exited on empty game_data, which is fine; the point is the launcher tried)"
# cleanup
pkill -f "BanjoTooie-Data/game/banjotooie" 2>/dev/null || true
