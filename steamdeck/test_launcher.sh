#!/usr/bin/env bash
# Test the standalone Linux launcher from a clean dir on ext4, like a player.
set -e
TEST="$HOME/bt_linux_test"
rm -rf "$TEST"; mkdir -p "$TEST"
cp /mnt/d/Temp/decomp/launcher/dist/Banjo-Tooie "$TEST/"
chmod +x "$TEST/Banjo-Tooie"
# Pre-seed the package path (valid JSON, forward slashes) so no file dialog needed.
cat > "$TEST/launcher_config.json" <<'EOF'
{ "package_path": "/mnt/d/Temp/decomp/ABB9CAB336175357D09F2D922735D23C62F90DDD58" }
EOF
export DISPLAY=:0
cd "$TEST"
setsid ./Banjo-Tooie >/tmp/bt_launcher.out 2>&1 < /dev/null &
echo "launched pid $!"
sleep 10
echo "=== provisioned game/ (should have banjotooie + .so, banjotooie executable) ==="
ls -la "$TEST/game" 2>/dev/null || echo "NO game/ dir yet"
echo "=== launcher stdout/stderr ==="
cat /tmp/bt_launcher.out 2>/dev/null | head -20
echo "=== is the GUI process alive? ==="
pgrep -af "Banjo-Tooie" | grep -v pgrep || echo "not running"
