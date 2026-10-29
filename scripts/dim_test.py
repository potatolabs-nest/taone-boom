#!/usr/bin/env python3
"""For every table record's inner block size N, test whether N == w*h*k for
entry fields (w,h) and small k -- i.e. whether the block is a raw image.
"""
import glob
import os
import struct
from collections import Counter

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def parse(b):
    if len(b) < 8:
        return None
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b) or c > 4096 or c == 0:
        return None
    entries = [[u32(b, o + 4 * j) for j in range(12)]
               for o in range(24, 24 + 48 * c, 48)]
    rest = b[hdr:]
    N = u32(rest, 0) if len(rest) >= 4 and u32(rest, 0) == len(rest) - 4 else len(rest)
    return c, hdr, entries, N


def main():
    hits = Counter()
    ratios = Counter()
    tot = 0
    examples = {}
    for arch in sorted(os.listdir(ASSETS)):
        d = os.path.join(ASSETS, arch)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.table"))):
            b = open(f, "rb").read()
            r = parse(b)
            if not r:
                continue
            c, hdr, entries, N = r
            if N < 16:
                continue
            tot += 1
            # collect plausible small dims from entry fields 0..11
            for e_i, e in enumerate(entries):
                for j in range(0, 12, 2):
                    a, bb = e[j], e[j + 1]
                    if 1 <= a < 4096 and 1 <= bb < 4096:
                        for k in (1, 2, 3, 4):
                            if a * bb * k == N:
                                key = f"e{e_i}[{j},{j+1}]*{k}"
                                hits[key] += 1
                                examples.setdefault(key, f)
            # ratio of N to the biggest dim pair seen
    print(f"total blocks N>=16: {tot}")
    print("exact w*h*k == N matches by (field pair, k):")
    for k, v in hits.most_common(20):
        print(f"   {v:6d}  {k}   eg {os.path.basename(examples[k])}")


if __name__ == "__main__":
    main()
