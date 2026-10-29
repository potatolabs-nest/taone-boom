#!/usr/bin/env python3
"""Decisive test: is a table payload a raw raster? Look for a row stride by
autocorrelation -- if the bytes are an image, byte[i] correlates with byte[i+w]
at the true width w (and its multiples).
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


def body(f):
    b = open(f, "rb").read()
    c = u32(b, 0)
    hdr = 24 + 48 * c
    pl = b[hdr:]
    if len(pl) >= 4 and u32(pl, 0) == len(pl) - 4:
        pl = pl[4:]
    return b, c, hdr, pl


def autocorr(pl, maxw=1200):
    n = len(pl)
    if n < 512:
        return []
    out = []
    for w in range(2, min(maxw, n // 2)):
        s = 0
        cnt = 0
        step = max(1, (n - w) // 4096)
        for i in range(0, n - w, step):
            d = pl[i] - pl[i + w]
            s += d * d
            cnt += 1
        out.append((s / cnt, w))
    return out


def main():
    files = []
    for f in glob.glob(os.path.join(ASSETS, "**/*.table"), recursive=True):
        try:
            b = open(f, "rb").read()
        except OSError:
            continue
        if len(b) >= 20000:
            files.append((len(b), f))
    files.sort(reverse=True)
    print(f"{len(files)} records >= 20000 bytes")
    for sz, f in files[:12]:
        b, c, hdr, pl = body(f)
        ac = autocorr(pl)
        if not ac:
            print(f"  {os.path.basename(f)} pl={len(pl)} too small")
            continue
        ac.sort()
        base = sum(x for x, _ in ac) / len(ac)
        best = ac[:6]
        print(f"\n{os.path.basename(f)}  size={sz} count={c} hdr={hdr} pl={len(pl)}")
        print(f"  mean sqdiff={base:.0f}  best strides (lowsqdiff, w)={' '.join(f'({int(a)},{w})' for a,w in best)}")
        # what fraction of variance is that
        print(f"  best/mean = {best[0][0]/base:.3f}")


if __name__ == "__main__":
    main()
