#!/usr/bin/env python3
"""Test: for icon-type records, is the block exactly w*h*3 raw 24bpp pixels?

Entry fields 8,9 looked like (w+2, h+2) -- a 2px border.  We test both the
frame size and the inner size, and render both if the byte count fits.
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pngwrite  # noqa: E402

OUT = "/Users/hieu/Workspaces/taone/work/table_probe"


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def parse(b):
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b) or not (0 < c <= 4096):
        return None
    ent = [[i32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    rest = b[hdr:]
    N = u32(rest, 0) if len(rest) >= 4 and u32(rest, 0) == len(rest) - 4 else len(rest)
    return c, hdr, ent, N, rest


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else "**/*icon.table"
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(
        f"/Users/hieu/Workspaces/taone/work/assets/by_index/{pat}", recursive=True))
    ok = 0
    m3 = 0
    print(f"{len(files)} files for {pat}")
    for f in files:
        b = open(f, "rb").read()
        r = parse(b)
        if not r:
            continue
        c, hdr, ent, N, rest = r
        e = ent[0]
        w, h, w2, h2 = e[6], e[7], e[8], e[9]
        cand = []
        for tag, W, H in (("f6,7", w, h), ("f8,9", w2, h2)):
            if W > 0 and H > 0 and W * H * 3 == N:
                cand.append((tag, W, H))
        if cand:
            ok += 1
            if ok <= 6:
                print(f"  {os.path.basename(f)} N={N} count={c} e0={e} -> {cand}")
    print(f"  exact w*h*3==N: {ok}/{len(files)}")


if __name__ == "__main__":
    main()
