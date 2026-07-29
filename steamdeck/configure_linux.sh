#!/usr/bin/env bash
# Configure the native-Linux (Vulkan) build of the Banjo-Tooie port in WSL.
#   wsl -d Ubuntu -- bash /mnt/d/Temp/decomp/steamdeck/configure_linux.sh
#
# Notes vs the CMakePresets defaults:
#  - linux-base hardcodes clang-20; this box has clang-21, so override to the
#    unversioned clang/clang++ (the `clang` metapackage -> clang-21).
#  - linux-amd64 preset omits -march; the SDK needs SSSE3/AVX2 intrinsics, same
#    as the Windows build. x86-64-v3 covers Steam Deck's Zen 2 APU.
set -euo pipefail
cd /mnt/d/Temp/decomp/banjotooie-recomp

cmake --preset linux-amd64-debug \
  -DREXSDK_DIR=/mnt/d/Temp/decomp/rexglue-sdk \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_C_FLAGS=-march=x86-64-v3 -DCMAKE_CXX_FLAGS=-march=x86-64-v3
