#!/usr/bin/env python3
"""Test the leading-descriptor + trailing-payload hypothesis on .table records.

Reported hypothesis from NOTES.md: a record opens with `u32 count | u32 2`,
followed by a rectangle table, 0xFFFFFFFF sentinels, and u16-pair sequences.

Here we test, without assuming:
  H1  u32[1] == 2                       (already known: 40,349/40,349)
  H2  the first `count` u32s are a descriptor table
  H3  somewhere near the end there is a length field == remaining bytes
  H4  a rectangle (x,y,w,h) elsewhere predicts the trailing data size
"""
import glob
import os
import struct
import sys
from collections import Counter

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def words(b, n=None):
    n = n or len(b) // 4
    return [u32(b, 4 * i) for i in range(n)]


def survey(pattern):
    """Across files matching a glob, report where a u32 == remaining bytes."""
    files = sorted(glob.glob(pattern))
    print(f"# {len(files)} files for {pattern}")
    hdr2 = 0
    hits = Counter()
    recty = Counter()
    for f in files:
        b = open(f, "rb").read()
        if len(b) < 8:
            continue
        if u32(b, 4) == 2:
            hdr2 += 1
        n = len(b) // 4
        for i in range(min(n, 64)):
            if u32(b, 4 * i) == len(b) - 4 * (i + 1) and i > 0:
                hits[i] += 1
        # rect-like: 4 consecutive u32 that are small and non-decreasing-ish
        for i in range(min(n - 3, 32)):
            a, c, d, e = (u32(b, 4 * (i + j)) for j in range(4))
            if 0 < a < 4096 and 0 < c < 4096 and 0 < d < 4096 and 0 < e < 4096:
                if d == a and e == c:
                    recty[i] += 1
    print(f"  u32[1]==2: {hdr2}/{len(files)}")
    print(f"  exact-length-field offsets (u32[i] == size-4*(i+1)): {hits.most_common(8)}")
    print(f"  (a,b,a,b) rectangle at offset i: {recty.most_common(10)}")
    print()


if __name__ == "__main__":
    survey(os.path.join(ASSETS, "FxStage/*.table"))
    survey(os.path.join(ASSETS, "CharTE/*.table"))
    survey(os.path.join(ASSETS, "FxCharacter/*.table"))
