#!/usr/bin/env python3
"""Probe the internal layout of Club Audition `table` records.

Established (NOTES.md / idd_layout_report.md): every payload is exact, named,
and most open with `u32 count | u32 2`.  This script tests the leading-descriptor
+ trailing-payload hypothesis without assuming it.
"""
import glob
import os
import struct
import sys

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def dump(path, n=200, maxu=64):
    b = open(path, "rb").read()
    print(f"### {os.path.basename(path)}  ({len(b)} bytes)")
    words = len(b) // 4
    for i in range(min(words, n)):
        v = u32(b, 4 * i)
        s = f"{v:,}" if v < 0x80000000 else f"{v - 2**32:,}"
        print(f"  0x{4*i:04x}: {v:>10d}  {b[4*i:4*i+4].hex(' ')}")
    if words > n:
        print(f"  ... ({words - n} more u32 words)")
    tail = b[4 * n:]
    if tail:
        print("  tail:", tail[:maxu].hex(" "), "..." if len(tail) > maxu else "")
    print()


if __name__ == "__main__":
    for a in sys.argv[1:]:
        dump(a)
