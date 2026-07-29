#!/usr/bin/env bash
export DISPLAY=:0
T="$HOME/bt_cap2"; rm -rf "$T"; mkdir -p "$T/BanjoTooie-Data"
cp /mnt/d/Temp/tooie/launcher/dist/Banjo-Tooie "$T/"; chmod +x "$T/Banjo-Tooie"
cat > "$T/BanjoTooie-Data/launcher_config.xml" <<'EOF'
<?xml version='1.0' encoding='utf-8'?>
<launcher><package_path>/mnt/d/Temp/tooie/ABB9CAB336175357D09F2D922735D23C62F90DDD58</package_path><auto_play>false</auto_play></launcher>
EOF
cd "$T"; setsid ./Banjo-Tooie >/tmp/c2.out 2>&1 </dev/null & sleep 8
WID=$(xwininfo -root -tree 2>/dev/null | grep "Banjo-Tooie PC Launcher" | head -1 | awk '{print $1}')
echo "wid ${WID:-none}"; [ -n "$WID" ] && import -window "$WID" /mnt/d/Temp/tooie/steamdeck/launcher_v2.png 2>/dev/null && echo ok
pkill -f "bt_cap2/Banjo-Tooie" 2>/dev/null; kill $(pgrep -f "bt_cap2") 2>/dev/null; rm -rf "$T"
