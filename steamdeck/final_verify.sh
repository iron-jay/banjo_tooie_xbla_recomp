#!/usr/bin/env bash
DIST=/mnt/d/Temp/decomp/launcher/dist/Banjo-Tooie
echo "=== launcher ELF glibc floor (must be <= Deck's 2.41) ==="
objdump -T "$DIST" 2>/dev/null | grep -oE 'GLIBC_[0-9]+\.[0-9]+' | sort -uV | tail -1
echo
export DISPLAY=:0
TEST="$HOME/bt_deck_test"
rm -rf "$TEST"; mkdir -p "$TEST"
cp "$DIST" "$TEST/"; chmod +x "$TEST/Banjo-Tooie"
cat > "$TEST/launcher_config.json" <<'EOF'
{ "package_path": "/mnt/d/Temp/decomp/ABB9CAB336175357D09F2D922735D23C62F90DDD58" }
EOF
cd "$TEST"
setsid ./Banjo-Tooie >/tmp/deck_launcher.out 2>&1 < /dev/null &
sleep 9
echo "=== provisioned game/ (expect RELEASE: banjotooie ~30MB, librexruntime.so, libTracyClient.so) ==="
ls -la "$TEST/game" 2>/dev/null || echo "no game dir"
echo "=== launcher stderr/stdout ==="
cat /tmp/deck_launcher.out | head -15
echo "=== launcher window in X? ==="
WID=$(xwininfo -root -tree 2>/dev/null | grep "Banjo-Tooie PC Launcher" | head -1 | awk '{print $1}')
echo "window id: ${WID:-none}"
if [ -n "$WID" ]; then
  import -window "$WID" /mnt/d/Temp/decomp/steamdeck/launcher_deck.png 2>/dev/null && echo "captured launcher_deck.png"
fi
