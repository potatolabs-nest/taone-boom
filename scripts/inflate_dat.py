#!/usr/bin/env python3
"""Inflate the FxDesktop `.dat` records (known zlib bin form) and parse the
resulting .table bytes. `*_mm` = minimap, so these should be real images.
"""
import glob
import os
import struct
import sys
import zlib


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def inflate_record(path):
    b = open(path, "rb").read()
    if len(b) < 8:
        return None
    cl, il = u32(b, 0), u32(b, 4)
    if cl != len(b) - 8:
        return None
    try:
        d = zlib.decompress(b[8:])
    except zlib.error:
        return None
    if len(d) != il:
        return None
    return d


def parse_table(b):
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b):
        return None
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    return c, hdr, ent, b[hdr:]


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else \
        "/Users/hieu/Workspaces/taone/work/assets/by_index/FxDesktop/*.dat"
    for p in sorted(glob.glob(pat)):
        d = inflate_record(p)
        if not d:
            print(f"{os.path.basename(p):-<50s} not a zlib record")
            continue
        r = parse_table(d)
        if not r:
            print(f"{os.path.basename(p):-<50s} inflated {len(d)} -> not a table")
            continue
        c, hdr, ent, rest = r
        print(f"{os.path.basename(p)}")
        print(f"   inflated={len(d)} count={c} hdr={hdr} rest={len(rest)}")
        for i, e in enumerate(ent[:6]):
            print(f"     e{i}: {e}")


if __name__ == "__main__":
    main()
