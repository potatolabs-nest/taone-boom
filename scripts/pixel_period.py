#!/usr/bin/env python3
"""Treat a .table payload as an array of 3-byte pixels and find the raster
width by pixel-level row autocorrelation.

If the block is a w-wide RGB raster, consecutive pixels are similar and
pixel[j] correlates strongly with pixel[j+w] (same column one row down), so the
mean |delta| at lag w (in PIXELS) is a clear local minimum.
"""
import glob
import os
import struct
import sys

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
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    return c, hdr, ent, r


def pixdelta(px, w, step=None):
    n = len(px)
    if w <= 0 or w >= n:
        return None
    st = step or max(1, (n - w) // 4000)
    s = 0
    cnt = 0
    for j in range(0, n - w, st):
        a = px[j]
        bb = px[j + w]
        s += abs(a[0] - bb[0]) + abs(a[1] - bb[1]) + abs(a[2] - bb[2])
        cnt += 1
    return s / max(cnt, 1)


def main():
    files = [(os.path.getsize(f), f) for f in
             glob.glob(os.path.join(ASSETS, "**/*.table"), recursive=True)]
    files.sort(reverse=True)
    shown = 0
    for sz, f in files:
        if shown >= 10:
            break
        c, hdr, ent, r = block(f)
        if len(r) < 3 * 40:
            continue
        px = [r[i:i + 3] for i in range(0, len(r) - 2, 3)]
        n = len(px)
        # candidate widths: those where w*3 divides N exactly, or nearly
        cands = []
        for w in range(2, min(n // 2, 3000)):
            if len(r) % (w * 3):
                continue
            d = pixdelta(px, w)
            if d is not None:
                cands.append((d, w, len(r) // (w * 3)))
        if not cands:
            continue
        cands.sort()
        base = pixdelta(px, 1)
        e0 = ent[0]
        print(f"\n{os.path.basename(f)} size={sz} count={c} N={len(r)} px={n}")
        print(f"  entry0 = {e0}")
        print(f"  adjacent-pixel delta={base:.1f}; best widths w (w*3 | N):")
        for d, w, h in cands[:6]:
            print(f"     w={w:5d} h={h:5d}  rowdelta={d:7.1f} rel={d/base:.3f}")
        shown += 1


if __name__ == "__main__":
    main()
