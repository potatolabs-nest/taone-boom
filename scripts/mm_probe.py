#!/usr/bin/env python3
"""Decode a minimap: .dat = [u32 cl][u32 il][zlib] -> table -> [u32 N][block].
Ground truth: entry fields (6,7) = (148,128) for every minimap.
"""
import struct
import sys
import zlib
from collections import Counter


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load(path):
    b = open(path, "rb").read()
    d = zlib.decompress(b[8:])
    c = u32(d, 0)
    hdr = 24 + 48 * c
    ent = [[u32(d, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    rest = d[hdr:]
    N = u32(rest, 0)
    assert N == len(rest) - 4, (N, len(rest))
    return ent, rest[4:]


def lagdeltas(pl, maxlag=32):
    n = len(pl)
    return [sum(abs(pl[i] - pl[i + l]) for i in range(0, n - l, max(1, (n - l) // 4000)))
            / max(1, (n - l) // max(1, (n - l) // 4000) or 1) for l in range(1, maxlag + 1)]


def main():
    p = sys.argv[1]
    ent, blk = load(p)
    print(f"{p}: entries={len(ent)} entry0={ent[0]} block={len(blk)}")
    w, h = ent[0][6], ent[0][7]
    print(f"  w={w} h={h} w*h={w*h} w*h*3={w*h*3} block/3={len(blk)/3}")
    # nested zlib?
    for off in range(0, 9):
        try:
            x = zlib.decompress(blk[off:])
            print(f"  nested zlib@{off} -> {len(x)}")
        except zlib.error:
            pass
    n = len(blk)
    base = sum(abs(blk[i] - blk[i + 1]) for i in range(0, n - 1, max(1, n // 4000))) / max(1, n // max(1, n // 4000))
    print(f"  adjacent-byte mean delta = {base:.2f}")
    print("  lags 1..32 (mean |delta|):")
    for l in range(1, 33):
        st = max(1, (n - l) // 4000)
        s = sum(abs(blk[i] - blk[i + l]) for i in range(0, n - l, st))
        c = len(range(0, n - l, st))
        v = s / c
        print(f"    lag {l:2d}: {v:6.2f} rel={v/base:.3f} {'#'*int(v/base*40)}")
    # byte histogram top
    print(f"  top bytes: {Counter(blk).most_common(12)}")
    print(f"  first 64: {blk[:64].hex(' ')}")
    print(f"  last 32 : {blk[-32:].hex(' ')}")


if __name__ == "__main__":
    main()
