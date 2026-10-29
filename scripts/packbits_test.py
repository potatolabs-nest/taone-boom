#!/usr/bin/env python3
"""Try real decompression schemes on `.table` blocks: PackBits and a few RLE
variants, and see which yields exactly (or nearly) w*h*3 bytes.
"""
import glob
import os
import struct
import sys
import zlib


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


def packbits(buf, start, limit):
    out = bytearray()
    i = start
    n = len(buf)
    while i < n:
        c = buf[i]
        i += 1
        if c < 128:
            cnt = c + 1
            out += buf[i:i + cnt]
            i += cnt
        elif c > 128:
            cnt = 257 - c
            if i >= n:
                break
            out += bytes([buf[i]]) * cnt
            i += 1
        if len(out) > limit:
            return bytes(out)
    return bytes(out)


def main():
    p = sys.argv[1]
    ent, blk = load(p)
    e = ent[0]
    w, h = e[6], e[7]
    tgt = w * h * 3
    print(f"{p}\n entry0={e} w*h*3={tgt} blk={len(blk)}")
    for start in range(0, 8):
        out = packbits(blk, start, tgt + tgt)
        tag = "EXACT" if len(out) == tgt else ("short" if len(out) < tgt else "long")
        print(f"  packbits start={start}: {len(out)} bytes ({tag})")
        if len(out) == tgt:
            return out
    return None


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main()
