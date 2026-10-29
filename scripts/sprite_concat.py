#!/usr/bin/env python3
"""Test: is a .table block a CONCATENATION of per-entry rasters?

If so, sum(w_i * h_i * 3) over entries == block length, and each entry's slice
renders as its own image.
"""
import glob
import os
import struct
import sys
import zlib

sys.path.insert(0, "/Users/hieu/Workspaces/taone/scripts")
import pngwrite  # noqa: E402

OUT = "/Users/hieu/Workspaces/taone/work/table_probe/sprites"


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load(p):
    b = open(p, "rb").read()
    if len(b) > 8 and u32(b, 0) == len(b) - 8:
        b = zlib.decompress(b[8:])
    c = u32(b, 0)
    hdr = 24 + 48 * c
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    blk = b[hdr:]
    if u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return ent, blk


def dims(e):
    """candidate (w,h) of an entry: fields 6,7 swapped check"""
    return e[6], e[7]


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else \
        "/Users/hieu/Workspaces/taone/work/assets/by_index/FxStage/00561_*.table"
    for p in sorted(glob.glob(pat)):
        ent, blk = load(p)
        print(f"\n{os.path.basename(p)} entries={len(ent)} block={len(blk)}")
        tot3 = sum(dims(e)[0] * dims(e)[1] * 3 for e in ent)
        tot1 = sum(dims(e)[0] * dims(e)[1] for e in ent)
        print(f"  sum(w*h*3)={tot3}  sum(w*h)={tot1}  block={len(blk)}")
        for i, e in enumerate(ent[:12]):
            w, h = dims(e)
            print(f"   e{i}: {e} -> w={w} h={h} w*h={w*h} w*h*3={w*h*3}")


if __name__ == "__main__":
    main()
