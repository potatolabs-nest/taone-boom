#!/usr/bin/env python3
"""Test whether a .table block is a TGA-family raster (header + raw/BGR pixels),
using a real TGA parser with several header variants.

The block for Lobby__Monster2_bt01 opens `ab 00 00 00 b0 00 00 00 ae 00 00 00
ba 00 00 00 00 00 00 00 00 00 00 00` = four small u32s then zeros -- also a
plausible 12-byte TGA header (idlen=0, cmap=0, type=0, cmap spec=0, x0=0, y0=0).
"""
import struct
import sys
import zlib

sys.path.insert(0, "/Users/hieu/Workspaces/taone/scripts")
import pngwrite  # noqa: E402

OUT = "/Users/hieu/Workspaces/taone/work/table_probe/tga"


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


def tga_parse(buf, hoff=0):
    """Parse a TGA header and return (w,h,pix,desc) or None."""
    if len(buf) < hoff + 18:
        return None
    idlen, cmap, imgtype = buf[hoff], buf[hoff + 1], buf[hoff + 2]
    cmapspec = struct.unpack_from("<HHB", buf, hoff + 3)
    x0, y0, w, h = struct.unpack_from("<HHHH", buf, hoff + 8)
    bpp, desc = buf[hoff + 16], buf[hoff + 17]
    if not (1 <= w <= 8192 and 1 <= h <= 8192):
        return None
    if imgtype not in (2, 3, 10, 11):
        return None
    nb = bpp // 8
    if nb not in (1, 2, 3, 4):
        return None
    start = hoff + 18 + idlen
    need = w * h * nb
    if start + need > len(buf):
        return None
    return {"w": w, "h": h, "bpp": bpp, "type": imgtype, "desc": desc,
            "start": start, "raw": buf[start:start + need]}


def main():
    for p in sys.argv[1:]:
        blk = load_block(p)
        print(f"\n{p}\n  block={len(blk)}")
        found = False
        for hoff in range(0, 20):
            r = tga_parse(blk, hoff)
            if r:
                print(f"   TGA hdr@{hoff}: {r['w']}x{r['h']} {r['bpp']}bpp "
                      f"type={r['type']} desc={r['desc']} start={r['start']}")
                found = True
        if not found:
            print("   no TGA header parses at offsets 0..19")
        # also: is there a plain u32 w,h at some offset?
        for o in range(0, 40, 4):
            a, b = u32(blk, o), u32(blk, o + 4)
            if 1 <= a <= 4096 and 1 <= b <= 4096:
                print(f"   u32 pair @{o}: w={a} h={b}  a*b={a*b} a*b*3={a*b*3} "
                      f"blk-{o+8}={len(blk)-o-8}")


if __name__ == "__main__":
    main()
