#!/usr/bin/env bash
set -e
cd /mnt/d/Temp/tooie/launcher
"$HOME/bt_venv/bin/python" build_release.py \
  /mnt/d/Temp/tooie/banjotooie-recomp/out/build/linux-amd64-debug
