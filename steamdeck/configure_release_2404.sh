#!/usr/bin/env bash
# Configure the glibc-portable RELEASE build (Vulkan) on Ubuntu 24.04.
#   wsl -d Ubuntu-24.04 -- bash <this>       (as the default user is fine)
# Same two preset overrides as the 26.04 build: pin clang (24.04 default is
# clang-18, we installed clang-21), and add -march (SDK needs SSSE3/AVX2).
set -euo pipefail
cd /mnt/d/Temp/decomp/banjotooie-recomp

cmake --preset linux-amd64-release \
  -DREXSDK_DIR=/mnt/d/Temp/decomp/rexglue-sdk \
  -DCMAKE_C_COMPILER=clang-21 -DCMAKE_CXX_COMPILER=clang++-21 \
  -DCMAKE_C_FLAGS=-march=x86-64-v3 -DCMAKE_CXX_FLAGS=-march=x86-64-v3
