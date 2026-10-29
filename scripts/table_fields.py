#!/usr/bin/env python3
"""Full-corpus analysis of .table records: field semantics + payload nature.

Layout under test (measured):  [24-byte prefix][count x 48-byte entry][payload]
Payload: u32 N followed by N bytes on 23,471 of 40,349 records; on the rest the
payload starts immediately.
"""
import glob
import json
import math
import os
import struct
import sys
import zlib
from collections import Counter, defaultdict

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def ent(b):
    if not b:
        return 0.0
    c = Counter(b)
    n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def parse(b):
    if len(b) < 8:
        return None
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b) or c > 4096 or c == 0:
        return None
    entries = [[i32(b, o + 4 * j) for j in range(12)]
               for o in range(24, 24 + 48 * c, 48)]
    return c, hdr, entries, b[hdr:]


def main():
    fieldnames = Counter()
    jdist = defaultdict(Counter)
    nrec = 0
    nentries = 0
    # signed/unsigned interpretation of each field over entries
    negsmall = Counter()
    zeros = Counter()
    minmax = defaultdict(lambda: [10 ** 9, -10 ** 9])
    paykind = Counter()
    selflen = 0
    plausible_rect = 0
    payload_ent = []
    for arch in sorted(os.listdir(ASSETS)):
        d = os.path.join(ASSETS, arch)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.table"))):
            b = open(f, "rb").read()
            r = parse(b)
            if not r:
                continue
            c, hdr, entries, pl = r
            nrec += 1
            nentries += len(entries)
            for e in entries:
                for j, v in enumerate(e):
                    jdist[j][v] += 1
                    if v == 0:
                        zeros[j] += 1
                    if v < 0:
                        negsmall[j] += 1
                    if v < minmax[j][0]:
                        minmax[j][0] = v
                    if v > minmax[j][1]:
                        minmax[j][1] = v
            if len(pl) >= 4 and u32(pl, 0) == len(pl) - 4:
                selflen += 1
                body = pl[4:]
            else:
                body = pl
            if len(body) >= 256:
                payload_ent.append(ent(body))
            if len(body) >= 16 and len(body) % 4 == 0:
                paykind["len%4==0"] += 1
                n0 = u32(body, 0)
                if 0 < n0 < len(body):
                    paykind["body0 small"] += 1
    print(f"records={nrec} entries={nentries} lenframed={selflen}")
    print("per-field signed-value stats (index: zero%, neg%, min, max, #distinct):")
    for j in range(12):
        tot = nentries
        mn, mx = minmax[j]
        print(f"  j={j:2d} zero={zeros[j]/tot*100:5.1f}% neg={negsmall[j]/tot*100:5.1f}% "
              f"min={mn:>12d} max={mx:>12d} distinct={len(jdist[j]):>7d} "
              f"top={[v for v,_ in jdist[j].most_common(5)]}")
    print("paykind:", paykind.most_common())
    if payload_ent:
        payload_ent.sort()
        n = len(payload_ent)
        print(f"payload entropy: min={payload_ent[0]:.2f} p25={payload_ent[n//4]:.2f} "
              f"med={payload_ent[n//2]:.2f} p75={payload_ent[3*n//4]:.2f} "
              f"max={payload_ent[-1]:.2f} over {n} blocks")


if __name__ == "__main__":
    main()
