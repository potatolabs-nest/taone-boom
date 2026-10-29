#!/usr/bin/env python3
"""Find every long match between the BMP's pixel array and the .table payload,
then print the bytes immediately BEFORE each match in the payload.  The header
that precedes a literal run is the token framing.
"""
import struct
import sys


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load_block(p):
    b = open(p, "rb").read()
    c = u32(b, 0)
    blk = b[24 + 48 * c:]
    if u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return blk


def bmp_pixels(p):
    b = open(p, "rb").read()
    w, h = struct.unpack_from("<ii", b, 18)
    off = struct.unpack_from("<I", b, 10)[0]
    stride = ((w * 3) + 3) // 4 * 4
    return w, h, bytes(x for y in range(h)
                       for x in b[off + (h - 1 - y) * stride:
                                  off + (h - 1 - y) * stride + w * 3])


def all_matches(pix, body, seed=24, minlen=32, step=1):
    idx = {}
    for i in range(0, len(pix) - seed, step):
        idx.setdefault(pix[i:i + seed], []).append(i)
    out = []
    j = 0
    n = len(body)
    while j < n - seed:
        s = body[j:j + seed]
        for pi in idx.get(s, [])[:1]:
            L = seed
            while pi + L < len(pix) and j + L < n and pix[pi + L] == body[j + L]:
                L += 1
            if L >= minlen:
                out.append((pi, j, L))
        j += 1
    return out


def main():
    blk = load_block(sys.argv[1])
    w, h, pix = bmp_pixels(sys.argv[2])
    print(f"block={len(blk)} bmp={w}x{h} pix={len(pix)}")
    m = all_matches(pix, blk)
    # dedup overlapping
    m.sort(key=lambda t: t[1])
    keep = []
    last = -1
    for pi, j, L in m:
        if j <= last:
            continue
        keep.append((pi, j, L))
        last = j
    print(f"{len(m)} raw matches, {len(keep)} non-overlapping")
    for pi, j, L in keep[:25]:
        pre = blk[max(0, j - 16):j]
        post = blk[j + L:j + L + 4]
        py = pi // (w * 3)
        px = (pi % (w * 3)) // 3
        print(f"  len={L:5d} body@{j:7d} pix@{pi:7d} (row {py}, col {px})")
        print(f"      pre={pre.hex(' ')}")
        print(f"      post={post.hex(' ')}")


if __name__ == "__main__":
    main()
