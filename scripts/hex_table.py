#!/usr/bin/env python3
"""Full hex + u32 view of a .table record, header vs payload split."""
import os
import struct
import sys

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]

def show(path, cap=512):
    b = open(path, "rb").read()
    n = len(b) // 4
    hits = [i for i in range(2, min(300, n)) if u32(b, 4*i) and 4*(i+1)+u32(b, 4*i) == len(b)]
    k = hits[0] if hits else None
    print(f"=== {os.path.basename(path)} size={len(b)} lenidx={hits[:5]}"
          + (f" hdr={4*k}" if k else ""))
    for i in range(0, len(b), 16):
        row = b[i:i+16]
        ws = " ".join(f"{u32(row,4*m):>8d}" if len(row) >= 4*m+4 else "     ..." for m in range(4))
        print(f" {i:6d}  {row.hex(' '):<47s} | {ws}")
    print()

if __name__ == "__main__":
    for p in sys.argv[1:]:
        show(p)
