#!/usr/bin/env python3
"""Dump a table record's payload bytes as hex, plus candidate interpretations."""
import os
import struct
import sys

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]

def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]

def main(path, want=384):
    b = open(path, "rb").read()
    c = u32(b, 0)
    hdr = 24 + 48 * c
    print(f"=== {os.path.basename(path)} size={len(b)} count={c} hdr={hdr}")
    print(f"  prefix: {[u32(b,4*j) for j in range(6)]}")
    for e in range(c):
        o = 24 + 48 * e
        print(f"  e{e}: {[u32(b,o+4*j) for j in range(12)]}")
    if hdr + 4 <= len(b):
        print(f"  u32@hdr = {u32(b,hdr)}  (remaining {len(b)-hdr-4})")
    pl = b[hdr:]
    print(f"  payload {len(pl)} bytes, first {want}:")
    for i in range(0, min(len(pl), want), 16):
        row = pl[i:i+16]
        fs = " ".join(f"{f32(row,4*m):>12.4g}" for m in range(len(row)//4))
        print(f"   {i:6d}  {row.hex(' '):<47s} | {fs}")
    if len(pl) > want:
        print(f"   ... {len(pl)-want} more bytes")
    print()

if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
