#!/usr/bin/env bash
BIN=/mnt/d/Temp/decomp/banjotooie-recomp/out/build/linux-amd64-debug/banjotooie
SO=/mnt/d/Temp/decomp/rexglue-sdk/out/linux-amd64/librexruntimed.so
echo "=== highest GLIBC_ symbol version required by banjotooie ==="
objdump -T "$BIN" 2>/dev/null | grep -oE 'GLIBC_[0-9]+\.[0-9]+' | sort -uV | tail -5
echo "=== highest GLIBCXX_ (libstdc++) required by banjotooie ==="
objdump -T "$BIN" 2>/dev/null | grep -oE 'GLIBCXX_[0-9]+\.[0-9]+' | sort -uV | tail -5
echo "=== highest GLIBC_ required by librexruntimed.so ==="
objdump -T "$SO" 2>/dev/null | grep -oE 'GLIBC_[0-9]+\.[0-9]+' | sort -uV | tail -5
echo "=== highest GLIBCXX_ required by librexruntimed.so ==="
objdump -T "$SO" 2>/dev/null | grep -oE 'GLIBCXX_[0-9]+\.[0-9]+' | sort -uV | tail -5
echo
echo "=== container / build-env tooling available in WSL ==="
for t in docker podman distrobox; do printf '%-10s ' $t; command -v $t >/dev/null && $t --version 2>/dev/null | head -1 || echo MISSING; done
echo "=== other WSL distros installed ==="
