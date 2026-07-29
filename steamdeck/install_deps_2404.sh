#!/usr/bin/env bash
# Toolchain for building a glibc-portable (Steam Deck) release on Ubuntu 24.04
# (glibc 2.39 - fits a Deck on glibc >= 2.39). Run as root:
#   wsl -d Ubuntu-24.04 -u root -- bash <this>
# 24.04 has cmake 3.28 (>=3.25) and GCC 13/14 (C++23) in-repo; only clang-21
# comes from apt.llvm.org (SDK needs clang >=20; 24.04 default is clang-18).
set -e
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y --no-install-recommends \
  wget gnupg ca-certificates lsb-release software-properties-common \
  cmake ninja-build pkg-config git python3 python3-venv python3-tk \
  libvulkan-dev vulkan-validationlayers spirv-tools \
  libx11-dev libxext-dev libxrandr-dev libxi-dev libxss-dev libxcursor-dev \
  libxinerama-dev libxfixes-dev libwayland-dev libdecor-0-dev \
  libpulse-dev libasound2-dev libgtk-3-dev libx11-xcb-dev

wget -qO /tmp/llvm.sh https://apt.llvm.org/llvm.sh
chmod +x /tmp/llvm.sh
/tmp/llvm.sh 21

echo "=== versions ==="
clang-21 --version | head -1
cmake --version | head -1
ninja --version
python3 --version
echo "glibc: $(ldd --version | head -1)"
