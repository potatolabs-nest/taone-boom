#!/usr/bin/env python3
"""Find the raster row stride in a .table payload by scanning lag = 3*w.

If the block is a w-wide 24bpp raster, byte[i] and byte[i+3w] are the same
colour channel one row down -> a strong local minimum at lag 3w.
"""
import struct
import sys
import zlib


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load(p):
    b = open(p, "rb").read()
    if b[:2] == b"\x78\xda" or (len(b) > 8 and u32(b, 0) == len(b) - 8):
        if u32(b, 0) == len(b) - 8:
            d = zlib.decompress(b[8:])
        else:
            d = zlib.decompress(b)
    else:
        d = b
    c = u32(d, 0)
    hdr = 24 + 48 * c
    ent = [[u32(d, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    rest = d[hdr:]
    N = u32(rest, 0)
    return ent, rest[4:4 + N]


def mdelta(pl, lag, budget=20000):
    n = len(pl)
    if lag >= n:
        return None
    st = max(1, (n - lag) // budget)
    s = 0
    c = 0
    for i in range(0, n - lag, st):
        s += abs(pl[i] - pl[i + lag])
        c += 1
    return s / c


def main():
    p = sys.argv[1]
    ent, blk = load(p)
    n = len(blk)
    w0, h0 = ent[0][6], ent[0][7]
    print(f"{p}\n  entry0={ent[0]} w={w0} h={h0} block={n} n%3={n%3}")
    base = mdelta(blk, 3)
    best = []
    for w in range(2, min(n // 3, 400)):
        d = mdelta(blk, 3 * w)
        if d is not None:
            best.append((d, w))
    best.sort()
    print(f"  mean|delta| at lag3 = {base:.2f}")
    print("  best row-widths w (lag=3w):")
    for d, w in best[:12]:
        print(f"    w={w:4d}  lag={3*w:6d}  delta={d:7.2f} rel={d/base:.3f}")


if __name__ == "__main__":
    main()
