#!/usr/bin/env python3
"""Test whether a table record's inner block is or contains a compressed stream,
and what its byte statistics look like.
"""
import glob
import math
import os
import struct
import sys
import zlib
from collections import Counter

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def inner(b):
    """Return (kind, hdr_len, N, block) for a table record."""
    if len(b) < 8:
        return None
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b):
        return None
    rest = b[hdr:]
    if len(rest) >= 4 and u32(rest, 0) == len(rest) - 4:
        return ("lenframed", hdr, len(rest) - 4, rest[4:])
    return ("raw", hdr, len(rest), rest)


def try_zlib(blk):
    for off in range(0, 8):
        for wbits in (15, -15, 47):
            try:
                d = zlib.decompressobj(wbits)
                out = d.decompress(blk[off:])
                if len(out) > 64:
                    return off, wbits, len(out)
            except Exception:
                pass
    return None


def ent(b):
    if not b:
        return 0.0
    c = Counter(b)
    n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def main():
    tot = Counter()
    zlibhits = []
    kinds = Counter()
    for arch in sorted(os.listdir(ASSETS)):
        d = os.path.join(ASSETS, arch)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.table"))):
            b = open(f, "rb").read()
            r = inner(b)
            if not r:
                continue
            kind, hdr, N, blk = r
            kinds[kind] += 1
            tot["n"] += 1
            if kind == "lenframed":
                tot["lenframed"] += 1
            if len(blk) >= 64:
                tot["nodes"] += 1
                h = try_zlib(blk)
                if h and len(zlibhits) < 10:
                    zlibhits.append((f, h, ent(blk), len(blk)))
    print("kinds:", kinds.most_common())
    print("tot:", dict(tot))
    print("zlib hits (file, (off,wbits,outlen), entropy, blocklen):")
    for z in zlibhits:
        print("  ", z)


if __name__ == "__main__":
    main()
