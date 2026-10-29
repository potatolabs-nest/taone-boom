#!/usr/bin/env python3
"""Large-scale structural test of .table records.

Parses [24-byte prefix][count x 48-byte entry][payload] where header_len is
taken as 24+48*count, then tests how the payload relates to the entries.
"""
import glob
import json
import math
import os
import struct
import sys
from collections import Counter

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")
ARCHS = ["FxStage", "CharTE", "FxCharacter", "FxMap", "fx", "EmoTE",
         "FxMonster", "FxDesktop", "FxContents", "FxHiddenCatch", "FxAsset"]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def parse(b):
    if len(b) < 8:
        return None
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b) or c > 4096:
        return None
    entries = []
    for e in range(c):
        o = 24 + 48 * e
        entries.append([u32(b, o + 4 * j) for j in range(12)])
    return c, hdr, entries, b[hdr:]


def main():
    stats = Counter()
    lead = Counter()
    per = {}
    samples = []
    for arch in ARCHS:
        files = sorted(glob.glob(os.path.join(ASSETS, arch, "*.table")))
        n = 0
        ok = 0
        for f in files:
            b = open(f, "rb").read()
            r = parse(b)
            if not r:
                continue
            c, hdr, entries, pl = r
            n += 1
            if hdr <= len(b):
                ok += 1
            for e in entries:
                for j, v in enumerate(e):
                    lead[j] = lead[j] if False else lead[j]
            # payload leading u32 vs entries
            if len(pl) >= 4:
                pl0 = u32(pl, 0)
                if pl0 == len(pl):
                    stats["payload_selflen"] += 1
                if pl0 == len(pl) - 4:
                    stats["payload_selflen4"] += 1
            # is payload length divisible by things
            if len(pl) and len(pl) % 4 == 0:
                stats["pl%4"] += 1
            # does any entry field == payload length?
            if any(v == len(pl) for e in entries for v in e):
                stats["entry_eq_plen"] += 1
            if any(v == len(pl) - 4 for e in entries for v in e):
                stats["entry_eq_plen4"] += 1
        per[arch] = {"files": n, "parsed": ok}
    print(json.dumps(per, indent=1))
    print("stats:", stats.most_common())


if __name__ == "__main__":
    main()
