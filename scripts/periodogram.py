#!/usr/bin/env python3
"""Periodogram of .table payloads: mean |byte[i]-byte[i+lag]| for lag 1..32.
A raw 24bpp raster shows a minimum at lag 3 (same channel next pixel) and at
lag 3w (same channel, next row).
"""
import glob
import os
import struct
from collections import Counter

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def block(f):
    b = open(f, "rb").read()
    c = u32(b, 0)
    hdr = 24 + 48 * c
    r = b[hdr:]
    if len(r) >= 4 and u32(r, 0) == len(r) - 4:
        r = r[4:]
    return c, r


def lagdeltas(pl, maxlag=32):
    n = len(pl)
    out = []
    for lag in range(1, maxlag + 1):
        st = max(1, (n - lag) // 6000)
        s = 0
        cnt = 0
        for i in range(0, n - lag, st):
            s += abs(pl[i] - pl[i + lag])
            cnt += 1
        out.append(s / max(cnt, 1))
    return out


def main():
    files = [(os.path.getsize(f), f) for f in
             glob.glob(os.path.join(ASSETS, "**/*.table"), recursive=True)]
    files.sort(reverse=True)
    agg = [0.0] * 32
    nn = 0
    for sz, f in files[:60]:
        c, pl = block(f)
        if len(pl) < 4000:
            continue
        d = lagdeltas(pl)
        for i in range(32):
            agg[i] += d[i]
        nn += 1
    agg = [x / nn for x in agg]
    print(f"aggregate over {nn} biggest records; mean |delta| by lag 1..32:")
    base = agg[0]
    for i, v in enumerate(agg):
        bar = "#" * int(v / base * 40)
        print(f"  lag {i+1:2d}: {v:6.2f}  rel={v/base:.3f} {bar}")


if __name__ == "__main__":
    main()
