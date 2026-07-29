#!/usr/bin/env bash
# Toolchain for building a glibc-portable (Steam Deck) release on Ubuntu 22.04
# (glibc 2.35). Run as root:
#   wsl -d Ubuntu-22.04 -u root -- bash <this>
# 22.04 ships clang-14 / cmake-3.22; the SDK needs clang >=20 and cmake >=3.25,
# so clang-21 comes from apt.llvm.org and a recent cmake from pip.
set -e
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y --no-install-recommends \
  wget gnupg ca-certificates lsb-release software-properties-common \
  ninja-build pkg-config git python3 python3-pip python3-venv python3-tk \
  libvulkan-dev vulkan-validationlayers spirv-tools \
  libx11-dev libxext-dev libxrandr-dev libxi-dev libxss-dev libxcursor-dev \
  libxinerama-dev libxfixes-dev libwayland-dev libdecor-0-dev \
  libpulse-dev libasound2-dev libgtk-3-dev libx11-xcb-dev

# clang 21 from the official LLVM apt repo (llvm.sh adds the repo + installs).
wget -qO /tmp/llvm.sh https://apt.llvm.org/llvm.sh
chmod +x /tmp/llvm.sh
/tmp/llvm.sh 21

# recent cmake (>=3.25) - 22.04's apt cmake is 3.22.
pip3 install --quiet cmake

echo "=== versions ==="
clang-21 --version | head -1
hash -r; cmake --version | head -1
ninja --version
python3 --version
echo "glibc: $(ldd --version | head -1)"
