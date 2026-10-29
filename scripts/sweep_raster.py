#!/usr/bin/env python3
"""Sweep (offset, width, bpp) and score row coherence vs a shuffled control.
A raw raster of the right width has MUCH lower adjacent-row difference than the
same bytes in random row order.  Renders the best few.
"""
import os
import random
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pngwrite  # noqa: E402

OUT = "/Users/hieu/Workspaces/taone/work/table_probe"


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load_table(p):
    b = open(p, "rb").read()
    if len(b) > 8 and u32(b, 0) == len(b) - 8:
        b = zlib.decompress(b[8:])
    c = u32(b, 0)
    hdr = 24 + 48 * c
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    rest = b[hdr:]
    N = u32(rest, 0)
    if N == len(rest) - 4:
        rest = rest[4:]
    return ent, rest


def rowwcoh(buf, off, w, h, bpp, rng):
    """Mean abs diff between adjacent rows (channel 0..bpp-1), vs shuffle."""
    stride = w * bpp
    rows = []
    for y in range(h):
        s = off + y * stride
        if s + stride > len(buf):
            return None, None
        rows.append(buf[s:s + stride])
    def coh(rs):
        t = 0
        c = 0
        step = max(1, stride // 64)
        for a, b in zip(rs, rs[1:]):
            for i in range(0, min(len(a), len(b)), step):
                t += (a[i] - b[i]) ** 2
                c += 1
        return t / max(c, 1)
    c0 = coh(rows)
    r2 = list(rows)
    rng.shuffle(r2)
    c1 = coh(r2)
    return c0, c1


def main():
    p = sys.argv[1]
    ent, blk = load_table(p)
    e = ent[0]
    w0, h0 = max(e[6], e[7]), min(e[6], e[7])
    print(f"{p}\n entry0={e} block={len(blk)}  w0={w0} h0={h0}")
    rng = random.Random(7)
    res = []
    for bpp in (3, 4):
        for w in range(max(2, w0 - 6), w0 + 7):
            for h in range(max(2, h0 - 6), h0 + 7):
                for off in range(0, 48):
                    c0, c1 = rowwcoh(blk, off, w, h, bpp, rng)
                    if c0 is None or not c1:
                        continue
                    res.append((c0 / c1, bpp, w, h, off, c0, c1))
    res.sort()
    print(" best (ratio<1 = coherent raster):")
    for r, bpp, w, h, off, c0, c1 in res[:20]:
        print(f"   bpp={bpp} w={w} h={h} off={off:2d} coh={c0:9.0f} "
              f"shuf={c1:9.0f} ratio={r:.3f}")

    # render top candidates
    os.makedirs(OUT, exist_ok=True)
    base = os.path.basename(p).rsplit(".", 1)[0]
    for i, (r, bpp, w, h, off, c0, c1) in enumerate(res[:5]):
        if bpp != 3:
            continue
        stride = w * 3
        need = stride * h
        buf = blk[off:off + need]
        if len(buf) < need:
            continue
        out = os.path.join(OUT, f"{base}_cand{i}_w{w}_h{h}_o{off}.png")
        pngwrite.png(out, w, h, buf, "RGB")
        print(f"   wrote {out}  ratio={r:.3f}")


if __name__ == "__main__":
    main()
