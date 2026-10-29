#!/usr/bin/env python3
"""Diagnose the 3-byte-interleave structure of a .table block and hunt for its
decompressor.

Ground truth: minimaps (`*_mm`) are 148x128 by entry[6],[7]. Two same-size
minimaps have DIFFERENT block sizes -> the block is compressed.
"""
import struct
import sys
import zlib
from collections import Counter


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


def channel_stats(blk, nch=3):
    print(f"  block={len(blk)} residue mod3={len(blk)%3}")
    for r in range(nch):
        ch = blk[r::nch]
        if not ch:
            continue
        c = Counter(ch)
        zeros = c.get(0, 0) / len(ch) * 100
        top = c.most_common(6)
        print(f"  chan[{r}] n={len(ch)} zero%={zeros:.1f} mean={sum(ch)/len(ch):.1f} "
              f"top={top}")


def rle_variants(blk, target):
    """Try common RLE schemes; return those whose output length == target."""
    res = []
    n = len(blk)

    def packbits_literal_high(ctrl_hi):
        out = bytearray()
        i = 0
        while i < n:
            c = blk[i]
            i += 1
            if ctrl_hi(c):
                cnt = (c & 0x7F) + 1
                if i >= n:
                    break
                out += bytes([blk[i]]) * cnt
                i += 1
            else:
                cnt = (c & 0x7F) + 1
                out += blk[i:i + cnt]
                i += cnt
        return len(out)

    res.append(("packbits hi>=0x80", packbits_literal_high(lambda c: c >= 0x80)))
    res.append(("packbits hi>0x80", packbits_literal_high(lambda c: c > 0x80)))

    def pair(cnt_first):
        out = bytearray()
        i = 0
        while i + 1 < n:
            a, b = blk[i], blk[i + 1]
            if cnt_first:
                out += bytes([b]) * a
            else:
                out += bytes([a]) * b
            i += 2
        return len(out)

    res.append(("pairs count,val", pair(True)))
    res.append(("pairs val,count", pair(False)))

    def control_byte(ctrlhi):
        out = bytearray()
        i = 0
        while i < n:
            c = blk[i]
            i += 1
            if c == 0:
                if i + 4 > n:
                    break
                out += blk[i:i + 4]
                i += 4
            elif ctrlhi and c >= 0x80:
                if i >= n:
                    break
                out += bytes([blk[i]]) * (c & 0x7F)
                i += 1
            else:
                out += bytes([c])
        return len(out)

    res.append(("ctrlbyte 0=lit4", control_byte(False)))
    return res


def try_decompress(blk, target):
    hits = []
    for off in range(0, 12):
        try:
            x = zlib.decompress(blk[off:])
            hits.append(("zlib", off, len(x)))
        except zlib.error:
            pass
        try:
            d = zlib.decompressobj(-15)
            x = d.decompress(blk[off:])
            if len(x) > 32:
                hits.append(("deflate-raw", off, len(x)))
        except zlib.error:
            pass
    return hits


def main():
    for p in sys.argv[1:]:
        ent, blk = load(p)
        e = ent[0]
        w, h = e[6], e[7]
        print(f"\n=== {p}")
        print(f"  entry0={e}  w*h={w*h} w*h*3={w*h*3} block={len(blk)} "
              f"deficit={w*h*3-len(blk)}")
        channel_stats(blk)
        print(f"  decompressors: {try_decompress(blk, w*h)}")
        print(f"  RLE output lengths (target {w*h*3} or {w*h}):")
        for name, out in rle_variants(blk, w * h * 3):
            print(f"     {name:22s} -> {out}")


if __name__ == "__main__":
    main()
