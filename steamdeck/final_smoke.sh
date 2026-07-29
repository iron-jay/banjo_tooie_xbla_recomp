#!/usr/bin/env bash
export DISPLAY=:0
TEST="$HOME/bt_final_test"
rm -rf "$TEST"; mkdir -p "$TEST/BanjoTooie-Data"
cp /mnt/d/Temp/tooie/launcher/dist/Banjo-Tooie "$TEST/"; chmod +x "$TEST/Banjo-Tooie"
cat > "$TEST/BanjoTooie-Data/launcher_config.xml" <<'EOF'
<?xml version='1.0' encoding='utf-8'?>
<launcher>
  <package_path>/mnt/d/Temp/tooie/ABB9CAB336175357D09F2D922735D23C62F90DDD58</package_path>
  <auto_play>false</auto_play>
</launcher>
EOF
cd "$TEST"
setsid ./Banjo-Tooie >/tmp/bt_final.out 2>&1 < /dev/null &
sleep 9
echo "=== files directly next to the launcher (should be JUST the launcher + BanjoTooie-Data) ==="
ls -1 "$TEST"
echo "=== BanjoTooie-Data structure ==="
find "$TEST/BanjoTooie-Data" -maxdepth 2 | sort | sed "s#$TEST/##"
echo "=== launcher stdout/stderr ==="
cat /tmp/bt_final.out | head
echo "=== capture window ==="
WID=$(xwininfo -root -tree 2>/dev/null | grep "Banjo-Tooie PC Launcher" | head -1 | awk '{print $1}')
echo "wid: ${WID:-none}"
[ -n "$WID" ] && import -window "$WID" /mnt/d/Temp/tooie/steamdeck/launcher_final.png 2>/dev/null && echo captured
