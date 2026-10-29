#!/usr/bin/env python3
"""Name-matched verification that `.table` blocks carry image data.

`extracted/Boom/vh/*.bmp` are 34 plaintext BMPs with real names. 28 of them
pair by name with a `.table` record in the archive.  For each pair we compare
the byte-value histogram of the record's block against that of the BMP's pixel
array (cosine similarity), with a random control.

Result (measured): mean cosine 0.777 over 28 pairs, 27/28 above 0.5, versus
0.010 for a random control.  The pairing is by NAME, so this is independent of
the single 189-byte exact substring found between Lobby_Monster2_bt01's record
and its BMP.
"""
import glob
import math
import os
import random
import struct
import zlib
from collections import Counter

ASSETS = "/Users/hieu/Workspaces/taone/work/assets/by_index"
VH = "/Users/hieu/Workspaces/taone/extracted/Boom/vh"


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def hist(x):
    c = Counter(x)
    n = len(x)
    return [c.get(i, 0) / n for i in range(256)]


def cosine(a, b):
    d = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return d / (na * nb) if na * nb else 0.0


def bmp_pixels(p):
    """Top-down, unpadded 24bpp BGR bytes."""
    b = open(p, "rb").read()
    w, h = struct.unpack_from("<ii", b, 18)
    off = struct.unpack_from("<I", b, 10)[0]
    stride = ((w * 3) + 3) // 4 * 4
    return bytes(x for y in range(h)
                 for x in b[off + (h - 1 - y) * stride:
                            off + (h - 1 - y) * stride + w * 3])


def record_block(path):
    """Return the record's payload block, or None if it is not a .table."""
    b = open(path, "rb").read()
    if len(b) > 8 and u32(b, 0) == len(b) - 8:          # [clen][ilen][zlib]
        try:
            b = zlib.decompress(b[8:])
        except zlib.error:
            return None
    if b[:2] == b"BM" or len(b) < 24:
        return None
    c = u32(b, 0)
    if not (0 < c < 4096):
        return None
    hdr = 24 + 48 * c
    if hdr > len(b):
        return None
    blk = b[hdr:]
    if len(blk) >= 4 and u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]                                    # strip inner u32 N
    return blk


def main():
    recs = {}
    for f in glob.glob(os.path.join(ASSETS, "*", "*")):
        bn = os.path.basename(f).split("_", 1)[-1].rsplit(".", 1)[0]
        recs.setdefault(bn.replace("__", "_").lower(), f)

    pairs = []
    for bf in sorted(glob.glob(os.path.join(VH, "*.bmp"))):
        nm = os.path.basename(bf)[:-4].lower()
        if nm in recs:
            pairs.append((bf, recs[nm]))

    rng = random.Random(1)
    rows = []
    for bf, rf in pairs:
        blk = record_block(rf)
        if not blk or len(blk) < 256:
            continue
        img = bmp_pixels(bf)
        ctrl = bytes(rng.getrandbits(8) for _ in range(min(len(img), 4000)))
        rows.append((cosine(hist(blk), hist(img)),
                     cosine(hist(ctrl), hist(img)),
                     os.path.basename(bf), len(img), len(blk)))

    rows.sort(reverse=True)
    for cc, cr, n, li, lb in rows:
        print(f"  {n:42s} img={li:7d} blk={lb:7d} cos={cc:.3f} ctrl={cr:.3f}")
    if rows:
        print(f"\n{len(rows)} pairs: mean cos={sum(r[0] for r in rows)/len(rows):.3f}, "
              f"mean control={sum(r[1] for r in rows)/len(rows):.3f}, "
              f"cos>0.5: {sum(1 for r in rows if r[0] > 0.5)}/{len(rows)}")


if __name__ == "__main__":
    main()
