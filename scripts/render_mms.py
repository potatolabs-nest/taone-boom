#!/usr/bin/env python3
"""Render every minimap `.dat` at its declared 148x128 to a contact sheet of
separate PNGs, plus a couple of transposed/offset variants, so the correct
layout can be identified by eye.
"""
import glob
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pngwrite  # noqa: E402

OUT = "/Users/hieu/Workspaces/taone/work/table_probe/mm"
ASSETS = "/Users/hieu/Workspaces/taone/work/assets/by_index"


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


def smooth2d(buf, w, h, bpp):
    """Mean |horizontal neighbour| + mean |vertical neighbour| (channel 0)."""
    stride = w * bpp
    need = stride * h
    if len(buf) < need:
        buf = buf + bytes(need - len(buf))
    hs = 0
    hc = 0
    vs = 0
    vc = 0
    for y in range(h):
        base = y * stride
        for x in range(0, w - 1):
            i = base + x * bpp
            hs += abs(buf[i] - buf[i + bpp])
            hc += 1
        if y + 1 < h:
            for x in range(0, w, max(1, w // 20)):
                i = base + x * bpp
                vs += abs(buf[i] - buf[i + stride])
                vc += 1
    return hs / max(hc, 1), vs / max(vc, 1)


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(ASSETS, "FxDesktop", "*_mm.dat")))
    for p in files:
        ent, blk = load(p)
        e = ent[0]
        w, h = e[6], e[7]
        name = os.path.basename(p).replace("_mm.dat", "").rsplit("_", 1)[-1]
        need = w * h * 3
        buf = blk[:need]
        if len(buf) < need:
            buf = buf + bytes(need - len(buf))
        pngwrite.png(os.path.join(OUT, f"{name}_{w}x{h}.png"), w, h, buf, "RGB")
        # transposed
        tr = bytearray()
        for x in range(w):
            for y in range(h):
                i = (y * w + x) * 3
                tr += buf[i:i + 3]
        pngwrite.png(os.path.join(OUT, f"{name}_{w}x{h}_T.png"), h, w, bytes(tr), "RGB")
        s = smooth2d(blk, w, h, 3)
        print(f"{name}: {w}x{h} block={len(blk)} need={need} "
              f"horiz_delta={s[0]:.1f} vert_delta={s[1]:.1f}")


if __name__ == "__main__":
    main()
