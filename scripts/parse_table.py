#!/usr/bin/env python3
"""Parse a .table record as:  [24-byte prefix][count x 48-byte entry]... then tail.

Header law measured across every archive: header_len == 24 + 48*count, verified
on all records where an exact trailing length field exists.
"""
import os
import struct
import sys

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]

def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]

def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]

def show(path, nshow=8):
    b = open(path, "rb").read()
    if len(b) < 4:
        return
    c = u32(b, 0)
    hdr = 24 + 48 * c
    print(f"=== {os.path.basename(path)} size={len(b)} count={c} hdr={hdr} tail={len(b)-hdr}")
    print(f"  PREFIX 24B: " + " ".join(f"{u32(b,4*j)}" for j in range(6)))
    for e in range(min(c, nshow)):
        o = 24 + 48 * e
        vals = [i32(b, o + 4 * j) for j in range(12)]
        fv = [f32(b, o + 4 * j) for j in range(12)]
        print(f"  entry[{e}] @{o}: i32={vals}")
        print(f"            f32={[round(x,4) for x in fv]}")
    if hdr + 16 <= len(b):
        print(f"  TAIL first 16 u32: {[u32(b,hdr+4*j) for j in range(min(16,(len(b)-hdr)//4))]}")
    print()

if __name__ == "__main__":
    for p in sys.argv[1:]:
        show(p)
