#!/usr/bin/env python3
"""Brute-force the RLE token layout of a .table block.

A token is 4 bytes: 3 colour bytes + 1 count byte. Test all 4 placements of the
count byte, both start offsets, and both 'count is the value' / 'count+1'.
Score = how close the decoded pixel count is to the entry's w*h.
"""
import glob
import os
import struct
import sys
import zlib
from collections import Counter

sys.path.insert(0, "/Users/hieu/Workspaces/taone/scripts")
import pngwrite  # noqa: E402


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


def decode(blk, start, cpos, cmode, bgr_order):
    """cpos: index 0..3 of the count byte within the 4-byte token.
    Returns (pixels, ntok)."""
    out = bytearray()
    i = start
    n = len(blk)
    ntok = 0
    while i + 3 < n:
        tk = blk[i:i + 4]
        cnt = tk[cpos]
        if cmode == "plus1":
            cnt += 1
        if cnt == 0:
            i += 4
            continue
        cb = bytes(tk[k] for k in range(4) if k != cpos)
        if bgr_order == "rgb":
            cb = cb[::-1]
        out += cb * cnt
        i += 4
        ntok += 1
        if len(out) > 400000:
            break
    return bytes(out), ntok


def main():
    pat = sys.argv[1]
    files = sorted(glob.glob(pat))[:6]
    for p in files:
        ent, blk = load(p)
        e = ent[0]
        w, h = e[6], e[7]
        tgt = w * h
        print(f"\n{os.path.basename(p)} entry0={e} w*h={tgt} blk={len(blk)}")
        res = []
        for cpos in range(4):
            for start in range(0, 8):
                for cmode in ("raw", "plus1"):
                    out, ntok = decode(blk, start, cpos, cmode, "bgr")
                    if ntok:
                        res.append((abs(len(out) - tgt), cpos, start, cmode,
                                    len(out), ntok))
        res.sort()
        for r in res[:6]:
            print(f"   cpos={r[1]} start={r[2]} mode={r[3]:5s} px={r[4]:7d} "
                  f"tok={r[5]:6d} off_by={r[0]}")


if __name__ == "__main__":
    main()
