#!/usr/bin/env python3
"""2-D period search over a .table block.

Find (dx, dy) such that byte[i] correlates with byte[i+dx] (horizontal neighbour)
and byte[i+dy] (vertical neighbour).  For a raster, dy == stride and dx == bpp.
"""
import struct
import sys
import zlib


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load(p):
    b = open(p, "rb").read()
    if len(b) > 8 and u32(b, 0) == len(b) - 8:
        b = zlib.decompress(b[8:])
    c = u32(b, 0)
    hdr = 24 + 48 * c
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    blk = b[hdr:]
    if u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return ent, blk


def md(blk, lag, budget=6000):
    n = len(blk)
    if lag >= n or lag <= 0:
        return None
    st = max(1, (n - lag) // budget)
    s = 0
    c = 0
    for i in range(0, n - lag, st):
        s += abs(blk[i] - blk[i + lag])
        c += 1
    return s / c


def main():
    ent, blk = load(sys.argv[1])
    n = len(blk)
    print(f"{sys.argv[1]}\n entries={len(ent)} e0={ent[0]} block={n}")
    # best small lags (horizontal period)
    small = sorted((md(blk, l), l) for l in range(1, 200))
    print(" best small lags (dx):")
    for d, l in small[:10]:
        print(f"   lag={l:4d} delta={d:.2f}")
    # best mid lags (vertical period)
    mid = sorted((md(blk, l), l) for l in range(200, min(n // 2, 3000)))
    print(" best mid lags (dy):")
    for d, l in mid[:10]:
        print(f"   lag={l:4d} delta={d:.2f}")


if __name__ == "__main__":
    main()
