#!/usr/bin/env python3
"""Broad RLE token brute force.

Search token size T=2..8, count byte position p, count mode (raw / +1 / +2),
and whether the non-count bytes are 1 or 3 colour bytes -- then score the
decoded length against w*h*3 (raw raster) or w*h (paletted).
Renders nothing; just reports the best layouts so a decoder can be eyeballed.
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


def try_layout(blk, T, p, mode, colour_bytes):
    out = bytearray()
    i = 0
    n = len(blk)
    while i + T <= n:
        tk = blk[i:i + T]
        cnt = tk[p]
        if mode == "p1":
            cnt += 1
        elif mode == "p2":
            cnt += 2
        if cnt == 0:
            i += T
            continue
        cb = bytes(tk[k] for k in range(T) if k != p)
        if colour_bytes == 1:
            cb = cb[:1]
        else:
            cb = cb[:3]
            if len(cb) < 3:
                cb = cb + bytes(3 - len(cb))
        out += cb * cnt
        i += T
        if len(out) > 1 << 21:
            return None
    return bytes(out)


def main():
    pat = sys.argv[1]
    for p in sorted(glob.glob(pat))[:3]:
        ent, blk = load(p)
        e = ent[0]
        w, h = e[6], e[7]
        targets = {"w*h*3": w * h * 3, "w*h": w * h, "w*h*4": w * h * 4}
        print(f"\n{os.path.basename(p)} entry0={e} blk={len(blk)} targets={targets}")
        res = []
        for T in range(2, 9):
            for cp in range(T):
                for mode in ("raw", "p1", "p2"):
                    for cb in (1, 3):
                        o = try_layout(blk, T, cp, mode, cb)
                        if not o:
                            continue
                        for tname, tg in targets.items():
                            if abs(len(o) - tg) <= max(8, tg * 0.01):
                                res.append((abs(len(o) - tg), T, cp, mode, cb,
                                            tname, len(o)))
        res.sort()
        seen = set()
        for r in res[:15]:
            key = (r[1], r[2], r[3], r[4], r[5])
            if key in seen:
                continue
            seen.add(key)
            print(f"   T={r[1]} cpos={r[2]} mode={r[3]:4s} cb={r[4]} -> "
                  f"{r[5]} len={r[6]}")
        if not res:
            print("   no layout reaches a target length")


if __name__ == "__main__":
    main()
