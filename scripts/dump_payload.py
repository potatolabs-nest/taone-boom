#!/usr/bin/env python3
"""Dump the header + payload boundary of chosen .table records in full detail."""
import os
import struct
import sys

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]

def show(path, nhdr=60, npl=160):
    b = open(path, "rb").read()
    n = len(b) // 4
    hits = [i for i in range(2, min(300, n)) if u32(b, 4*i) and 4*(i+1)+u32(b, 4*i) == len(b)]
    print(f"=== {os.path.basename(path)} size={len(b)} lenfield_u32idx={hits}")
    if not hits:
        return
    k = hits[0]
    hdr = b[:4*k]
    print(f"  HEADER {len(hdr)} bytes as u32 x{len(hdr)//4}:")
    for j in range(0, len(hdr)//4, 6):
        row = hdr[4*j:4*j+24]
        print(f"   [{j:3d}] " + " ".join(f"{u32(row,4*m):>10d}" for m in range(min(6, len(row)//4))))
        print(f"        " + " ".join(f"{row[4*m:4*m+4].hex():>10s}" for m in range(min(6, len(row)//4))))
    print(f"  LEN={u32(b,4*k)}  PAYLOAD {len(b)-4*(k+1)} bytes:")
    pl = b[4*(k+1):]
    for j in range(0, min(len(pl)//4, npl//4)):
        w = pl[4*j:4*j+4]
        print(f"   p[{j:4d}] {u32(pl,4*j):>10d}  {w.hex(' ')}")
    rem = pl[4*(npl//4):]
    if rem:
        print(f"   + {len(rem)} bytes: {rem[:64].hex(' ')}")
    print()

if __name__ == "__main__":
    for p in sys.argv[1:]:
        show(p)
