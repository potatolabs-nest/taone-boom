#!/usr/bin/env python3
"""Inside each `.table` block, find the longest run of 4-byte units whose 4th
byte is 0xFF (opaque alpha) -- i.e. a raw BGRA pixel array.
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
    if hdr > len(b):
        return None
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    blk = b[hdr:]
    if len(blk) >= 4 and u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return ent, blk


def longest_alpha_run(blk, phase):
    best = 0
    besto = -1
    cur = 0
    start = phase
    for i in range(phase, len(blk), 4):
        if blk[i] == 255:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best = cur
                besto = start
        else:
            cur = 0
    return best, besto


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else "FxStage/*.table"
    files = sorted(glob.glob(
        f"/Users/hieu/Workspaces/taone/work/assets/by_index/{pat}", recursive=True))
    print(f"{len(files)} files")
    rows = []
    for f in files[:4000]:
        r = load(f)
        if not r:
            continue
        ent, blk = r
        if len(blk) < 64:
            continue
        best = max((longest_alpha_run(blk, ph) for ph in range(4)),
                   key=lambda t: t[0])
        e = ent[0]
        rows.append((best[0], best[1], len(blk), f, e[6], e[7]))
    rows.sort(reverse=True)
    for n, o, bl, f, w, h in rows[:15]:
        print(f"  run={n:6d} at off={o:7d} block={bl:8d} w={w} h={h} "
              f"{os.path.basename(f)}")


if __name__ == "__main__":
    main()
