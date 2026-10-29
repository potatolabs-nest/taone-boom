#!/usr/bin/env python3
"""Derive the .table header law: is header_len == 24 + f(count) ?"""
import glob
import os
import struct
from collections import Counter, defaultdict

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def len_field(b, lo=2, hi=2000):
    n = len(b) // 4
    for i in range(lo, min(hi, n)):
        v = u32(b, 4 * i)
        if 0 < v and 4 * (i + 1) + v == len(b):
            return i, v
    return None, None


def main():
    for arch in ("FxStage", "CharTE", "FxCharacter", "FxMap", "fx", "EmoTE",
                 "FxMonster", "FxDesktop", "FxContents", "FxHiddenCatch"):
        files = sorted(glob.glob(os.path.join(ASSETS, arch, "*.table")))
        if not files:
            continue
        rel = Counter()
        cnt_max = 0
        bad = []
        for f in files:
            b = open(f, "rb").read()
            if len(b) < 8:
                continue
            c = u32(b, 0)
            cnt_max = max(cnt_max, c)
            hi = 24 + 4 * c + 8  # only look just around the 24+4c prediction
            k, v = len_field(b, max(2, (24 + 4 * c) // 4 - 4), min(len(b) // 4, (24 + 4 * c) // 4 + 40))
            if k is None:
                continue
            hdr = 4 * k
            rel[(hdr - 24) // 4 / max(c, 1) if c else None] += 1
            if c and hdr not in (24 + 4 * c, 24 + 48 * c, 24 + 8 * c):
                if len(bad) < 4:
                    bad.append((os.path.basename(f), len(b), c, hdr, u32(b, 4)))
        print(f"# {arch}: {len(files)} tables, max count {cnt_max}")
        print(f"  (hdr-24)/4/c ratio histogram: {rel.most_common(8)}")
        for x in bad:
            print(f"    nonstandard: {x}")
        print()


if __name__ == "__main__":
    main()
