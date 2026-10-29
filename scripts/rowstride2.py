#!/usr/bin/env python3
"""Search for a raster width w such that (a) 3*w divides the block length and
(b) byte[i] correlates strongly with byte[i+3w] (row-to-row coherence).

If the block is a raw 3-byte-per-pixel image of width w, byte i and byte i+3w
are the SAME colour channel one row apart -> strong correlation.
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


def parse(f):
    b = open(f, "rb").read()
    c = u32(b, 0)
    hdr = 24 + 48 * c
    entries = [[u32(b, o + 4 * j) for j in range(12)]
               for o in range(24, 24 + 48 * c, 48)]
    rest = b[hdr:]
    if len(rest) >= 4 and u32(rest, 0) == len(rest) - 4:
        rest = rest[4:]
    return c, hdr, entries, rest


def rowscore(pl, w, step=1):
    """mean |delta| between byte i and byte i+w over the block (1-D, no bpp)."""
    n = len(pl)
    if w <= 0 or w >= n:
        return None
    s = 0
    cnt = 0
    st = max(1, (n - w) // 8192)
    for i in range(0, n - w, st):
        s += abs(pl[i] - pl[i + w])
        cnt += 1
    return s / max(cnt, 1)


def main():
    files = []
    for f in glob.glob(os.path.join(ASSETS, "**/*.table"), recursive=True):
        if os.path.getsize(f) >= 3000:
            files.append((os.path.getsize(f), f))
    files.sort(reverse=True)
    for sz, f in files[:8]:
        c, hdr, entries, pl = parse(f)
        n = len(pl)
        base = rowscore(pl, 1)  # adjacent-byte mean delta
        cands = []
        # candidate widths: multiples of 3 that divide
        for w in range(6, min(n // 3, 4000), 3):
            if n % w:
                continue
            sc = rowscore(pl, w)
            if sc is not None:
                cands.append((sc, w, n // w))
        cands.sort()
        prod = 1
        for _, w, h in cands[:6]:
            prod *= 0
        print(f"\n{os.path.basename(f)} size={sz} count={c} hdr={hdr} N={n}")
        print(f"  adjacent byte delta {base:.1f}; best widths dividing N:")
        for sc, w, h in cands[:8]:
            print(f"    w={w:5d} h={h:5d}  ratio_vs_adj={sc/base:.3f}  (3w divides: yes)")


if __name__ == "__main__":
    main()
