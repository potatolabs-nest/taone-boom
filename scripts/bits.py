#!/usr/bin/env python3
"""Test bitstream hypotheses on a .table block: the payload is measurably
image-derived but matches no byte-oriented codec, which points at a
bit-oriented code (Huffman/arithmetic).

Strategy: estimate the marginal symbol entropy.  For a code that emits one
symbol per pixel per channel, the block's bit budget is 8*len(block) bits, so
the mean bits/pixel = 8*len(block)/(w*h).  If that lands near a plausible
entropy for the image, the block is a bit-exact entropy code of the raster.
"""
import math
import struct
import sys
import zlib
from collections import Counter

sys.path.insert(0, "/Users/hieu/Workspaces/taone/scripts")
import pngwrite  # noqa: E402


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


def ent(x):
    if not x:
        return 0.0
    c = Counter(x)
    n = len(x)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def main():
    p = sys.argv[1]
    w = int(sys.argv[2])
    h = int(sys.argv[3])
    blk = load_block(p)
    npx = w * h
    print(f"{p}\n block={len(blk)} raster={w}x{h} ({npx} px)")
    print(f"  block bytes/pixel        = {len(blk)/npx:.4f}")
    print(f"  bits/pixel               = {8*len(blk)/npx:.3f}")
    print(f"  bits/pixel/channel       = {8*len(blk)/(npx*3):.3f}")
    print(f"  block 1st-order entropy  = {ent(blk):.3f} bits/byte "
          f"(=> {ent(blk)/8*len(blk):,.0f} bytes minimum for a plain codec)")
    # unique byte count vs image
    print(f"  distinct byte values     = {len(set(blk))}")
    # how many distinct values in the whole 16-bit and 12-bit views
    from collections import Counter as C
    u16 = C(int.from_bytes(blk[i:i+2], 'little') for i in range(0, len(blk)-1, 2))
    print(f"  distinct u16 values      = {len(u16)}; top={u16.most_common(5)}")


if __name__ == "__main__":
    main()
