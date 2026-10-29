#!/usr/bin/env python3
"""Sweep candidate raster widths over the WHOLE block and score adjacent-row
coherence vs a shuffled control. No reliance on the entry fields.
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
    blk = b[hdr:]
    N = u32(blk, 0)
    if N == len(blk) - 4:
        blk = blk[4:]
    return ent, blk


def coh(buf, stride, rng, budget=3000):
    n = len(buf)
    h = n // stride
    if h < 4:
        return None
    rows = [buf[i * stride:(i + 1) * stride] for i in range(h)]
    step = max(1, stride // 40)

    def sc(rs):
        t = 0
        c = 0
        for a, b in zip(rs, rs[1:]):
            for i in range(0, min(len(a), len(b)), step):
                t += (a[i] - b[i]) ** 2
                c += 1
        return t / max(c, 1)

    c0 = sc(rows)
    r2 = list(rows)
    rng.shuffle(r2)
    c1 = sc(r2)
    return c0, c1, h


def main():
    p = sys.argv[1]
    ent, blk = load_table(p)
    print(f"{p}\n entries={len(ent)} block={len(blk)}")
    print(f" entry0={ent[0]}")
    rng = random.Random(11)
    res = []
    for stride in range(4, 3000):
        if len(blk) // stride < 8:
            break
        r = coh(blk, stride, rng)
        if r:
            res.append((r[0] / r[1], stride, r[0], r[1], r[2]))
    res.sort()
    print(" best strides (ratio = coherence vs shuffled; <<1 means real raster):")
    for ratio, stride, c0, c1, h in res[:20]:
        print(f"   stride={stride:5d} rows={h:5d} coh={c0:9.0f} shuf={c1:9.0f} "
              f"ratio={ratio:.3f}")
    print(" worst strides:")
    for ratio, stride, c0, c1, h in res[-5:]:
        print(f"   stride={stride:5d} rows={h:5d} ratio={ratio:.3f}")
    base = os.path.basename(p).rsplit(".", 1)[0]
    os.makedirs(OUT, exist_ok=True)
    for i, (ratio, stride, c0, c1, h) in enumerate(res[:3]):
        need = stride * h
        if stride % 3:
            continue
        w = stride // 3
        buf = blk[:need]
        out = os.path.join(OUT, f"{base}_sweep{i}_w{w}_h{h}.png")
        pngwrite.png(out, w, h, buf, "RGB")
        print(f"   wrote {out} ({w}x{h}) ratio={ratio:.3f}")


if __name__ == "__main__":
    main()
