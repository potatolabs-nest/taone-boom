#!/usr/bin/env python3
"""Test the hypothesis that a .table payload is a raw 3-byte-per-pixel raster,
and derive its width from the entry descriptor rather than guessing.

Layout under test:
    [24-byte prefix][count x 48-byte entry][u32 N][N bytes of pixel data]
Entry fields (index -> meaning, candidate):
    6,7  = (w, h) copy of prefix[4],[5]
    10   = w   (== field 6)
    11   = h   (== field 7)
So the block should be w*h*3 bytes.
"""
import glob
import os
import struct
import sys
import zlib
from collections import Counter

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def parse(b):
    if len(b) < 8:
        return None
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b) or not (1 <= c <= 4096):
        return None
    entries = [[i32(b, o + 4 * j) for j in range(12)]
               for o in range(24, 24 + 48 * c, 48)]
    rest = b[hdr:]
    if len(rest) >= 4 and u32(rest, 0) == len(rest) - 4:
        return c, hdr, entries, rest[4:], True
    return c, hdr, entries, rest, False


def report():
    """How often does w*h*3 == len(block) using the candidate w/h fields?"""
    tot = 0
    c_ok = Counter()
    for arch in sorted(os.listdir(ASSETS)):
        d = os.path.join(ASSETS, arch)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.table"))):
            b = open(f, "rb").read()
            r = parse(b)
            if not r:
                continue
            c, hdr, entries, blk, lf = r
            if len(blk) < 3:
                continue
            tot += 1
            e0 = entries[0]
            for (w, h, tag) in ((e0[6], e0[7], "6,7"), (e0[10], e0[11], "10,11"),
                                (e0[8], e0[9], "8,9"), (e0[6], e0[7], "66")):
                if w > 0 and h > 0 and w * h * 3 == len(blk):
                    c_ok[tag] += 1
    print(f"blocks>=3: {tot}")
    for k, v in c_ok.most_common():
        print(f"  w*h*3==len using fields({k}): {v}  ({v/tot*100:.1f}%)")


if __name__ == "__main__":
    report()
