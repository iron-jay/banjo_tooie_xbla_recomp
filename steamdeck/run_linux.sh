#!/usr/bin/env bash
# Run the native-Linux (Vulkan) Banjo-Tooie build under WSLg.
set -u
BUILD=/mnt/d/Temp/decomp/banjotooie-recomp/out/build/linux-amd64-debug
export LD_LIBRARY_PATH=/mnt/d/Temp/decomp/rexglue-sdk/out/linux-amd64:${LD_LIBRARY_PATH:-}
# Keep user data / shader cache on the fast ext4 home, not the slow 9p /mnt.
export REX_USER_DATA_ROOT="$HOME/bt_userdata"
export REX_MNK_MODE=true
export REX_KEYBIND_START=Return
mkdir -p "$REX_USER_DATA_ROOT"
cd "$BUILD"
exec ./banjotooie --game_data_root /mnt/d/Temp/decomp/xbla/files --log-level debug
