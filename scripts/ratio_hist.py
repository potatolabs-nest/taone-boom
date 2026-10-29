#!/usr/bin/env python3
"""Across the corpus, histogram block_len / (w*h) using the entry dimension
fields, to find the pixel-format distribution.
"""
import glob
import os
import struct
from collections import Counter

ASSETS = "/Users/hieu/Workspaces/taone/work/assets/by_index"


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def parse(b):
    if len(b) < 8:
        return None
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b) or not (0 < c <= 4096):
        return None
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    blk = b[hdr:]
    if len(blk) >= 4 and u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return ent, blk


def main():
    ratios = Counter()
    per_arch = {}
    exact1 = 0
    exact3 = 0
    exact4 = 0
    tot = 0
    samples = {}
    for arch in sorted(os.listdir(ASSETS)):
        d = os.path.join(ASSETS, arch)
        if not os.path.isdir(d):
            continue
        n = 0
        for f in sorted(glob.glob(os.path.join(d, "*.table"))):
            b = open(f, "rb").read()
            r = parse(b)
            if not r:
                continue
            ent, blk = r
            e = ent[0]
            # try the several dim pairs
            best = None
            for (W, H, tag) in ((e[6], e[7], "6,7"), (e[4], e[5], "4,5"),
                                (e[8], e[9], "8,9"), (e[10], e[11], "10,11")):
                if 1 <= W < 65536 and 1 <= H < 65536:
                    area = W * H
                    if area and abs(len(blk) / area - 1) < 0.02 and (
                            best is None or abs(len(blk) / area - 1)
                            < abs(best[0])):
                        best = (len(blk) / area, tag, W, H)
            if best:
                exact1 += 1
                samples.setdefault("1:1", (f, best))
            n += 1
            tot += 1
            e0 = ent[0]
            if e0[6] and e0[7]:
                ratios[round(len(blk) / (e0[6] * e0[7]), 2)] += 1
        per_arch[arch] = n
    print(f"total parsed: {tot}")
    print(f"records whose block_len ~= w*h (<2% off) via some field pair: {exact1}")
    for k, v in samples.items():
        f, best = v
        print(f"   eg {k}: {os.path.basename(f)} ratio={best[0]:.4f} via {best[1]} "
              f"W={best[2]} H={best[3]}")
    print(f"ratio histogram using fields(6,7): {ratios.most_common(20)}")


if __name__ == "__main__":
    main()
