#!/usr/bin/env python3
"""Compare a .table record's block against the plaintext BMP of the same asset.

`extracted/Boom/vh/Lobby_Monster2_bt01.bmp` is 171x880 24bpp; the table record
`FxStage/00561_Lobby__Monster2_bt01.table` has prefix [8,2,4,12,880,171].
Test whether the BMP's pixel bytes appear inside the table block, and at what
transform.
"""
import struct
import sys


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load_table(p):
    b = open(p, "rb").read()
    c = u32(b, 0)
    hdr = 24 + 48 * c
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    rest = b[hdr:]
    N = u32(rest, 0) if u32(rest, 0) == len(rest) - 4 else len(rest)
    return b, c, hdr, ent, rest[:N]


def load_bmp(p):
    b = open(p, "rb").read()
    assert b[:2] == b"BM"
    off = struct.unpack_from("<I", b, 10)[0]
    w, h = struct.unpack_from("<ii", b, 18)
    bpp = struct.unpack_from("<H", b, 28)[0]
    return b, off, w, h, bpp, b[off:]


def main():
    tp, bp = sys.argv[1], sys.argv[2]
    b, c, hdr, ent, blk = load_table(tp)
    raw, off, w, h, bpp, pix = load_bmp(bp)
    stride = ((w * bpp // 8) + 3) // 4 * 4
    print(f"table {tp}: count={c} hdr={hdr} block={len(blk)}")
    print(f"  prefix={[u32(b,4*j) for j in range(6)]}")
    for i, e in enumerate(ent):
        print(f"  e{i}: {e}")
    print(f"bmp {bp}: {w}x{h} {bpp}bpp stride={stride} pixbytes={len(pix)}")
    # unique-ish BMP row search in block
    row0 = pix[0:stride]
    idx = blk.find(row0)
    print(f"  bmp row0 ({stride}B) inside table block at: {idx}")
    # try matching a sub-slice of the bmp row (drop padding)
    row0u = pix[0:w * 3]
    for name, needle in (("row0_unpadded", row0u), ("row0_first64", row0u[:64]),
                         ("pix_unpadded_first1024",
                          b"".join(pix[y * stride:y * stride + w * 3]
                                   for y in range(4)))):
        print(f"  {name}: find -> {blk.find(needle)}")
    print(f"  block[0:64] = {blk[:64].hex(' ')}")
    print(f"  bmp  pix[0:64] = {pix[:64].hex(' ')}")
    # are the block's first bytes a permutation of the bmp's?
    print(f"  block[0:16] as bmp-shaped {w}x{h} 3bpp? need {w*h*3}, have {len(blk)}")
    print(f"  block/{w*h} = {len(blk)/(w*h):.4f}   block/(w*h*4) = {len(blk)/(w*h*4):.4f}")


if __name__ == "__main__":
    main()
