#!/usr/bin/env python3
"""Corpus-wide test of the 24bpp-interleave signature.

A byte stream whose 3 channels are stored interleaved has mean|delta(lag 3)|
markedly LOWER than at lags 1, 2, 4 and 5, because lag-3 differences are
within-channel.  Measure the fraction of records showing this.
"""
import glob
import os
import struct
from collections import Counter

ASSETS = "/Users/hieu/Workspaces/taone/work/assets/by_index"


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load_block(b):
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b):
        return None
    blk = b[hdr:]
    if len(blk) >= 4 and u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return blk


def md(buf, lag, budget=1500):
    n = len(buf)
    if lag >= n:
        return None
    st = max(1, (n - lag) // budget)
    s = 0
    c = 0
    for i in range(0, n - lag, st):
        s += abs(buf[i] - buf[i + lag])
        c += 1
    return s / c


def main():
    tot = 0
    sig3 = 0
    by_arch = Counter()
    tot_arch = Counter()
    for arch in sorted(os.listdir(ASSETS)):
        d = os.path.join(ASSETS, arch)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.table"))):
            b = open(f, "rb").read()
            if len(b) < 64:
                continue
            blk = load_block(b)
            if not blk or len(blk) < 600:
                continue
            tot += 1
            tot_arch[arch] += 1
            d1, d2, d3 = md(blk, 1), md(blk, 2), md(blk, 3)
            d4, d5 = md(blk, 4), md(blk, 5)
            if None in (d1, d2, d3, d4, d5):
                continue
            others = min(d1, d2, d4, d5)
            if d3 < 0.75 * others:
                sig3 += 1
                by_arch[arch] += 1
    print(f"records tested            : {tot:,}")
    print(f"show 24bpp interleave sig : {sig3:,} ({sig3/tot*100:.1f}%)")
    print("per archive (sig/total):")
    for a in sorted(tot_arch):
        print(f"  {a:14s} {by_arch[a]:6d}/{tot_arch[a]:6d} "
              f"({by_arch[a]/max(tot_arch[a],1)*100:5.1f}%)")


if __name__ == "__main__":
    main()
