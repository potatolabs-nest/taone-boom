#!/usr/bin/env python3
"""Dump every entry of a big .table record, plus the payload framing."""
import os
import struct
import sys


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


def main(path):
    b = open(path, "rb").read()
    c = u32(b, 0)
    hdr = 24 + 48 * c
    print(f"=== {os.path.basename(path)} size={len(b)} count={c} hdr={hdr}")
    print(f"  prefix u32: {[u32(b,4*j) for j in range(6)]}")
    for e in range(c):
        o = 24 + 48 * e
        print(f"  e{e:2d}: u32={[u32(b,o+4*j) for j in range(12)]}")
        print(f"       f32={[round(f32(b,o+4*j),4) for j in range(12)]}")
    rest = b[hdr:]
    print(f"  rest={len(rest)} bytes; u32[0]={u32(rest,0)}; "
          f"u32[0]==len-4? {u32(rest,0)==len(rest)-4}")
    if u32(rest, 0) == len(rest) - 4:
        rest = rest[4:]
    print(f"  block={len(rest)} bytes; block/3={len(rest)/3}")
    for e in range(c):
        o = 24 + 48 * e
        w, h = u32(b, o + 24), u32(b, o + 28)
        if w and h:
            print(f"    e{e}: w={w} h={h} w*h*3={w*h*3}")
    # dump first bytes as raw + as 3-byte pixels
    print("  first 60 bytes:", rest[:60].hex(" "))
    print("  first 20 px   :", [tuple(rest[3*i:3*i+3]) for i in range(20)])


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
