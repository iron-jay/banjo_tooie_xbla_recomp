#!/usr/bin/env bash
# Build the portable Linux launcher against the 24.04 RELEASE binaries.
set -e
if [ ! -d "$HOME/bt_venv" ]; then
  python3 -m venv --system-site-packages "$HOME/bt_venv"
fi
"$HOME/bt_venv/bin/pip" install --quiet --upgrade pip pyinstaller 2>&1 | tail -2
cd /mnt/d/Temp/tooie/launcher
"$HOME/bt_venv/bin/python" build_release.py \
  /mnt/d/Temp/tooie/banjotooie-recomp/out/build/linux-amd64-release
