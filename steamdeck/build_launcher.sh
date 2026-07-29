#!/usr/bin/env bash
set -e
cd /mnt/d/Temp/decomp/launcher
"$HOME/bt_venv/bin/python" build_release.py \
  /mnt/d/Temp/decomp/banjotooie-recomp/out/build/linux-amd64-debug
