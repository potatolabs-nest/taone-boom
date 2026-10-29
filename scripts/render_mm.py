#!/usr/bin/env python3
"""Render candidate interpretations of a minimap block and report which look
like real images (structure present, not uniform, not noise).

Design line search: a real minimap must show spatial coherence.  We measure
that by comparing the *row-to-row* similarity of a candidate raster against
its shuffled control.
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pngwrite  # noqa: E402

OUT = "/Users/hieu/Workspaces/taone/work/table_probe"


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
    rest = b[hdr:]
    N = u32(rest, 0)
    return ent, rest[4:4 + N]


def coherence(rows):
    """Mean squared difference between adjacent rows; low = structured."""
    tot = 0
    cnt = 0
    for a, b in zip(rows, rows[1:]):
        for x, y in zip(a, b):
            tot += (x - y) ** 2
            cnt += 1
    return tot / cnt


def main():
    os.makedirs(OUT, exist_ok=True)
    base = "00192_Etc__MonS2Fire_mm"
    p = f"/Users/hieu/Workspaces/taone/work/assets/by_index/FxDesktop/{base}.dat"
    ent, blk = load(p)
    w, h = ent[0][6], ent[0][7]
    n = len(blk)
    print(f"{base}: w={w} h={h} block={n}")

    # candidate A: block IS the raster (may be short/long)
    need = w * h * 3
    cands = {}
    for name, buf, nch in [
        ("A_take_exact", blk[:need], 3),
        ("A_pad", blk + bytes(max(0, need - n)), 3),
        ("B_halves", blk, 3),
    ]:
        if len(buf) >= need:
            cands[name] = (buf[:need], nch)
    # candidate C: 16-bit? 2 bytes/px
    if n >= w * h * 2:
        cands["C_16bpp"] = (blk[:w * h * 2], 2)

    for name, (buf, nch) in cands.items():
        px = [tuple(buf[y * w * nch + x * nch + k] for k in range(nch))
              for y in range(h) for x in range(w)]
        st = pngwrite.stats(buf[:w * h * nch])
        # row coherence of the R channel
        rows = [[buf[(y * w + x) * nch] for x in range(w)] for y in range(h)]
        coh = coherence(rows)
        # shuffle control: same bytes, random row order
        rows2 = list(rows)
        import random
        random.Random(1).shuffle(rows2)
        coh2 = coherence(rows2)
        pix = buf[:w * h * nch] if nch == 3 else None
        out = os.path.join(OUT, f"{base}_{name}.png")
        if nch == 3:
            pngwrite.png(out, w, h, pix, "RGB")
        print(f"  {name:12s} nch={nch} mean={st['mean']:.1f} std={st['std']:.1f} "
              f"distinct={st['distinct']} topfrac={st['frac_top']:.3f} "
              f"rowcoh={coh:.0f} shuffled={coh2:.0f} -> {out}")


if __name__ == "__main__":
    main()
