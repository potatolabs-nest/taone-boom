#!/usr/bin/env python3
"""Test PNG-style per-scanline filtering on a .table block.

If the block is `[filter_byte][w*bpp bytes]` repeated, the filter byte explains
both the image-like byte statistics and the absence of any standard codec match.
We brute force (stride, filter-byte position, whether the filter byte is at the
start of each row) and un-filter, then score against the ground-truth BMP.
"""
import struct
import sys

sys.path.insert(0, "/Users/hieu/Workspaces/taone/scripts")
import pngwrite  # noqa: E402

OUT = "/Users/hieu/Workspaces/taone/work/table_probe/filt"


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load_block(p):
    b = open(p, "rb").read()
    if len(b) > 8 and u32(b, 0) == len(b) - 8:
        b = __import__("zlib").decompress(b[8:])
    c = u32(b, 0)
    blk = b[24 + 48 * c:]
    if u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return blk


def unfilter(data, stride, bpp, nrows):
    """Apply PNG filters. data: rows of (stride+1) starting with a filter byte."""
    out = bytearray()
    prev = bytes(stride)
    for r in range(nrows):
        base = r * (stride + 1)
        f = data[base]
        row = bytearray(data[base + 1:base + 1 + stride])
        if f == 1:
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif f == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                left = row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                c = prev[i - bpp] if i >= bpp else 0
                bb = prev[i]
                pa, pb, pc = abs(bb - c), abs(a - c), abs(a + bb - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (bb if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF
        elif f not in (0, 1, 2, 3, 4):
            return None
        out += row
        prev = bytes(row)
    return bytes(out)


def main():
    blk = load_block(sys.argv[1])
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 171
    print(f"block={len(blk)} w={w}")
    for bpp in (3, 4, 1):
        stride = w * bpp
        for fpos in ("pre", "post"):
            rlen = stride + 1
            nrows = len(blk) // rlen
            if nrows < 8:
                continue
            # is the filter byte at row start or row end?
            if fpos == "pre":
                data = blk[:nrows * rlen]
            else:
                # move the last byte of each row to the front
                data = bytearray()
                for r in range(nrows):
                    row = blk[r * rlen:(r + 1) * rlen]
                    data += bytes([row[-1]]) + row[:-1]
                data = bytes(data)
            # filter byte histogram
            fbytes = [data[r * rlen] for r in range(nrows)]
            from collections import Counter
            hist = Counter(fbytes).most_common(4)
            out = unfilter(data, stride, bpp, nrows)
            print(f"  bpp={bpp} {fpos}: rows={nrows} filterbytes={hist}")
            if out and bpp == 3:
                pngwrite.png(f"{OUT}_{fpos}_b{bpp}.png", w, nrows, out, "RGB")


if __name__ == "__main__":
    main()
