#!/usr/bin/env python3
"""Locate the payload-length field and characterise the trailing payload."""
import glob
import math
import os
import struct
import sys
from collections import Counter

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def ent(b):
    if not b:
        return 0.0
    c = Counter(b)
    n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def find_len_field(b, lo=2, hi=260):
    """All i where u32[i] == remaining bytes after the field (exact)."""
    n = len(b) // 4
    out = []
    for i in range(lo, min(hi, n)):
        v = u32(b, 4 * i)
        if 0 < v <= len(b) and 4 * (i + 1) + v == len(b):
            out.append(i)
    return out


def report(pattern, label, nsample=6):
    files = sorted(glob.glob(pattern))
    off = Counter()
    exact = 0
    samples = []
    for f in files:
        b = open(f, "rb").read()
        hits = find_len_field(b)
        if hits:
            exact += 1
            k = hits[0]
            off[k] += 1
            if len(samples) < nsample:
                samples.append((f, k, b))
    print(f"# {label}: {exact}/{len(files)} files have an exact trailing length field")
    print(f"  header length (u32 index of the len field) histogram: {off.most_common(12)}")
    for f, k, b in samples:
        hdrlen = 4 * k
        plen = u32(b, hdrlen)
        pl = b[hdrlen + 4:]
        print(f"  {os.path.basename(f)} size={len(b)} hdr={hdrlen} plen={plen} "
              f"ent={ent(pl):.2f}")
        print(f"     hdr u32s[0:14]: {[u32(b,4*j) for j in range(min(14,k))]}")
    print()


if __name__ == "__main__":
    report(os.path.join(ASSETS, "FxStage/*.table"), "FxStage")
    report(os.path.join(ASSETS, "CharTE/*.table"), "CharTE")
    report(os.path.join(ASSETS, "FxCharacter/*.table"), "FxCharacter")
    report(os.path.join(ASSETS, "FxMap/*.table"), "FxMap")
