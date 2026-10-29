#!/usr/bin/env python3
"""Brute-force decompression search over a .table block: zlib, raw deflate,
gzip, bz2, lzma, at every offset 0..1024, accepting partial output.
"""
import bz2
import lzma
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
    rest = b[hdr:]
    N = u32(rest, 0)
    return rest[4:4 + N], 24 + 48 * c


def main():
    for p in sys.argv[1:]:
        blk, hdr = load(p)
        print(f"\n=== {p} block={len(blk)}")
        best = []
        for off in range(0, min(1025, len(blk))):
            sub = blk[off:]
            # raw deflate
            for wb in (-15, 15, 47):
                try:
                    d = zlib.decompressobj(wb)
                    out = d.decompress(sub)
                    out += d.flush()
                    if len(out) > 2000:
                        best.append((len(out), f"deflate wb={wb} off={off}"))
                except Exception:
                    pass
            if off < 64:
                for name, fn in (("bz2", bz2.decompress), ("lzma", lzma.decompress)):
                    try:
                        out = fn(sub)
                        if len(out) > 2000:
                            best.append((len(out), f"{name} off={off}"))
                    except Exception:
                        pass
        best.sort(reverse=True)
        if not best:
            print("  no decompressor succeeded anywhere")
        for n, tag in best[:8]:
            print(f"  {tag}: {n:,}")


if __name__ == "__main__":
    main()
