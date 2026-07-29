#!/usr/bin/env bash
REL=/mnt/d/Temp/decomp/banjotooie-recomp/out/build/linux-amd64-release/banjotooie
SO=/mnt/d/Temp/decomp/rexglue-sdk/out/linux-amd64/librexruntime.so
TR=/mnt/d/Temp/decomp/rexglue-sdk/out/linux-amd64/libTracyClient.so
command -v objdump >/dev/null || { echo "installing binutils"; apt-get install -y binutils >/dev/null 2>&1; }
for f in "$REL" "$SO" "$TR"; do
  echo "=== $(basename "$f") ==="
  echo "  max GLIBC:   $(objdump -T "$f" 2>/dev/null | grep -oE 'GLIBC_[0-9]+\.[0-9]+' | sort -uV | tail -1)"
  echo "  max GLIBCXX: $(objdump -T "$f" 2>/dev/null | grep -oE 'GLIBCXX_[0-9]+\.[0-9.]+' | sort -uV | tail -1)"
  echo "  NEEDED libs: $(objdump -p "$f" 2>/dev/null | awk '/NEEDED/{printf "%s ",$2}')"
done