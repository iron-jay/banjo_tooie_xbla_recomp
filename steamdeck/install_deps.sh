#!/usr/bin/env bash
# Install the Linux/Vulkan build toolchain + SDL deps for the Banjo-Tooie
# native-Linux (Steam Deck) bring-up. Run as root inside WSL Ubuntu:
#   wsl -d Ubuntu -u root -- bash /mnt/d/Temp/tooie/steamdeck/install_deps.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "=== apt-get update ==="
apt-get update -y

echo "=== apt-get install toolchain + deps ==="
apt-get install -y --no-install-recommends \
  clang cmake ninja-build git pkg-config \
  libvulkan-dev vulkan-validationlayers spirv-tools \
  libx11-dev libxext-dev libxrandr-dev libxi-dev libxss-dev libxcursor-dev \
  libxinerama-dev libxfixes-dev libwayland-dev libdecor-0-dev \
  libpulse-dev libasound2-dev

echo "=== DONE. Versions: ==="
clang --version | head -1
cmake --version | head -1
ninja --version
pkg-config --modversion vulkan 2>/dev/null && echo "vulkan pkg-config OK" || echo "vulkan pkg-config: (n/a)"
