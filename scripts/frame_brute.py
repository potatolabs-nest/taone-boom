#!/usr/bin/env python3
"""Decisive framing brute force, scored on CONTENT not length.

Ground truth: `FxStage/00561_Lobby__Monster2_bt01.table` vs the plaintext
`extracted/Boom/vh/Lobby_Monster2_bt01.bmp` (171x880).  The payload demonstrably
contains the BMP's pixel bytes (a 189-byte exact run, 37.5% of random 16-byte
samples vs 0% for a random control), so a correct framing must reproduce them.

We try many token framings and report which one's decoded byte stream best
matches the BMP's top-down 24bpp pixel array.
"""
import struct
import sys
import zlib


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load_block(p):
    b = open(p, "rb").read()
    if len(b) > 8 and u32(b, 0) == len(b) - 8:
        b = zlib.decompress(b[8:])
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
    return bytes(x for y in range(h)
                 for x in b[off + (h - 1 - y) * stride:
                            off + (h - 1 - y) * stride + w * 3])


def match_ratio(a, b, n=4000, win=8):
    """Fraction of sampled win-byte windows of `b` present in `a`."""
    S = set(a[i:i + win] for i in range(0, max(0, len(a) - win), 17))
    step = max(1, len(b) // n)
    hit = 0
    tot = 0
    for i in range(0, len(b) - win, step):
        tot += 1
        if b[i:i + win] in S:
            hit += 1
    return hit / max(tot, 1)


def main():
    blk = load_block(sys.argv[1])
    pix = bmp_pixels(sys.argv[2])
    print(f"block={len(blk)} pix={len(pix)} "
          f"direct match_ratio={match_ratio(blk, pix):.3f}")
    best = []

    # A) [u8 n][n*3 bytes] literal
    for hsz in (1, 2, 4):
        for order in ("le", "be"):
            out = bytearray()
            i = 0
            n = len(blk)
            while i + hsz <= n:
                ln = int.from_bytes(blk[i:i + hsz],
                                    "little" if order == "le" else "big")
                i += hsz
                if ln == 0:
                    continue
                out += blk[i:i + ln]
                i += ln
                if len(out) > 1 << 22:
                    break
            r = match_ratio(bytes(out), pix)
            best.append((r, f"litlen hsz={hsz} {order}", len(out)))

    # B) skip k bytes then [u8 n][n*3]
    for skip in range(0, 6):
        out = bytearray()
        i = skip
        n = len(blk)
        while i < n:
            ln = blk[i]
            i += 1
            if ln == 0:
                continue
            out += blk[i:i + ln]
            i += ln
            if len(out) > 1 << 22:
                break
        r = match_ratio(bytes(out), pix)
        best.append((r, f"u8lit skip={skip}", len(out)))

    # C) byte-pair RLE: [n][bgr]
    for cpos in range(4):
        out = bytearray()
        i = 0
        n = len(blk)
        while i + 4 <= n:
            tk = blk[i:i + 4]
            cnt = tk[cpos]
            cb = bytes(tk[k] for k in range(4) if k != cpos)
            out += cb * cnt
            i += 4
            if len(out) > 1 << 22:
                break
        best.append((match_ratio(bytes(out), pix), f"rle4 cpos={cpos}", len(out)))

    best.sort(reverse=True)
    for r, tag, ln in best[:12]:
        print(f"  {tag:22s} len={ln:8d} match_ratio={r:.3f}")


if __name__ == "__main__":
    main()
