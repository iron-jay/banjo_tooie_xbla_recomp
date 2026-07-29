"""Minimal Xbox 360 STFS ('LIVE'/'PIRS'/'CON ') package extractor.

Only implements flat file-listing enumeration and raw block extraction -
no signature/hash verification, no directory nesting (the Banjo-Tooie XBLA
package doesn't use subdirectories). ReXGlue decrypts/decompresses the XEX
itself, so this only needs to pull the STFS container's raw files out to
disk - no XEX2 decryption here.

Byte offsets for the 0x40-byte file-listing entries were reverse-engineered
and validated against a known-good prior extraction (all 35 real files in
the reference package matched byte-for-byte, including the largest
50MB+ file) - see D:\\Temp\\decomp\\CLAUDE.md "Launcher" section for how.
"""
from __future__ import annotations

import re
import struct
import os
from dataclasses import dataclass

_VALID_NAME_RE = re.compile(r"^[A-Za-z0-9_.\- ]+$")

BLOCK_SIZE = 0x1000
BLOCKS_PER_HASH_TABLE = 0xAA  # 170

# Files the game expects under game:\RAWFiles\<name> in addition to the
# top-level copy the STFS package stores them as. See CLAUDE.md "Data layout
# gotcha - RAWFiles".
RAWFILES_NAMES = (
    "xarialuni.ttf",
    "X360_strings.dat",
    "banjo2_360.tbl",
    "banjo2_360.ctl",
    "db360.cmp",
    "db360.textures.cmp",
    "ArcadeNormal.ptc",
    "ArcadeWide.ptc",
    "ArcadeInfo.xml",
)


def _read_uint24_le(b: bytes, off: int) -> int:
    return b[off] | (b[off + 1] << 8) | (b[off + 2] << 16)


@dataclass
class StfsFileEntry:
    name: str
    start_block: int
    file_size: int
    path_indicator: int


class StfsPackage:
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self.data = f.read()
        magic = self.data[0:4]
        if magic not in (b"LIVE", b"PIRS", b"CON "):
            raise ValueError(f"not an STFS package (magic={magic!r}): {path}")
        self.magic = magic
        self.header_size = struct.unpack_from(">I", self.data, 0x340)[0]
        vd = self.data[0x379 : 0x379 + 0x24]
        self.file_table_block_count = struct.unpack_from("<H", vd, 0x2)[0]
        self.file_table_block_number = _read_uint24_le(vd, 0x4)
        self.base_offset = (self.header_size + 0xFFF) & ~0xFFF

    def _hash_blocks_before(self, block_num: int) -> int:
        """Number of hash-table blocks interspersed before logical block
        `block_num`, across the hierarchy levels STFS uses."""
        count = block_num // BLOCKS_PER_HASH_TABLE + 1
        if block_num >= BLOCKS_PER_HASH_TABLE:
            count += block_num // (BLOCKS_PER_HASH_TABLE * BLOCKS_PER_HASH_TABLE) + 1
            if block_num >= BLOCKS_PER_HASH_TABLE * BLOCKS_PER_HASH_TABLE:
                count += 1
        return count

    def _block_offset(self, block_num: int) -> int:
        backing_block = block_num + self._hash_blocks_before(block_num)
        return self.base_offset + backing_block * BLOCK_SIZE

    def _read_block(self, block_num: int) -> bytes:
        off = self._block_offset(block_num)
        return self.data[off : off + BLOCK_SIZE]

    def read_file_data(self, start_block: int, file_size: int) -> bytes:
        num_blocks = (file_size + BLOCK_SIZE - 1) // BLOCK_SIZE
        parts = [self._read_block(start_block + i) for i in range(num_blocks)]
        return b"".join(parts)[:file_size]

    def list_files(self) -> list[StfsFileEntry]:
        table_bytes = bytearray()
        for i in range(self.file_table_block_count):
            table_bytes += self._read_block(self.file_table_block_number + i)

        entries = []
        for i in range(len(table_bytes) // 0x40):
            rec = table_bytes[i * 0x40 : (i + 1) * 0x40]
            if rec[0] == 0:
                continue
            name_flag = rec[0x28]
            name_len = name_flag & 0x3F
            if name_len == 0 or name_len > 0x28:
                continue
            try:
                name = rec[0:name_len].decode("ascii")
            except UnicodeDecodeError:
                continue
            if not _VALID_NAME_RE.match(name):
                continue
            start_block = _read_uint24_le(rec, 0x2F)
            path_indicator = struct.unpack_from(">h", rec, 0x32)[0]
            file_size = struct.unpack_from(">I", rec, 0x34)[0]
            # Sanity bounds: reject entries whose claimed size or start
            # block can't fit in the package at all - filters out
            # leftover/deleted table slots that happened to pass the name
            # check (their block/size fields are stale garbage).
            if file_size > len(self.data):
                continue
            if start_block * BLOCK_SIZE > len(self.data):
                continue
            entries.append(StfsFileEntry(name, start_block, file_size, path_indicator))
        return entries

    def extract_all(self, out_dir: str, progress=None) -> list[str]:
        """Extract every file entry (skipping directory placeholders, i.e.
        zero-size entries) to `out_dir`. Also populates a RAWFiles\\
        subdirectory with copies of the files the game additionally expects
        there. Returns the list of extracted file names."""
        os.makedirs(out_dir, exist_ok=True)
        rawfiles_dir = os.path.join(out_dir, "RAWFiles")
        os.makedirs(rawfiles_dir, exist_ok=True)

        files = self.list_files()
        real_files = [f for f in files if f.file_size > 0]
        extracted = []
        for idx, entry in enumerate(real_files):
            if progress:
                progress(idx, len(real_files), entry.name)
            data = self.read_file_data(entry.start_block, entry.file_size)
            out_path = os.path.join(out_dir, entry.name)
            with open(out_path, "wb") as f:
                f.write(data)
            extracted.append(entry.name)
            if entry.name in RAWFILES_NAMES:
                with open(os.path.join(rawfiles_dir, entry.name), "wb") as f:
                    f.write(data)
        if progress:
            progress(len(real_files), len(real_files), "done")
        return extracted
