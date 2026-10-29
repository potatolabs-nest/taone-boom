#!/usr/bin/env python3
"""Try LZ4 / Snappy block decoders on `.table` blocks.

A strong test: `FxStage/00561_Lobby__Monster2_bt01.table` holds the same art as
the plaintext BMP `extracted/Boom/vh/Lobby_Monster2_bt01.bmp`, so a correct
decompressor must reproduce exactly that BMP's pixel bytes.
"""
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
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    blk = b[hdr:]
    if u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return ent, blk


def lz4_decode(src, start=0, limit=1 << 22):
    out = bytearray()
    i = start
    n = len(src)
    while i < n:
        tok = src[i]
        i += 1
        ll = tok >> 4
        if ll == 15:
            while i < n and src[i] == 255:
                ll += 255
                i += 1
            if i >= n:
                break
            ll += src[i]
            i += 1
        out += src[i:i + ll]
        i += ll
        if i + 2 > n:
            break
        off = src[i] | (src[i + 1] << 8)
        i += 2
        if off == 0 or off > len(out):
            return bytes(out), "bad-offset"
        ml = (tok & 0xF) + 4
        if (tok & 0xF) == 15:
            while i < n and src[i] == 255:
                ml += 255
                i += 1
            if i >= n:
                break
            ml += src[i]
            i += 1
        for _ in range(ml):
            out.append(out[-off])
        if len(out) > limit:
            return bytes(out), "limit"
    return bytes(out), "ok"


def snappy_decode(src, limit=1 << 22):
    # varint uncompressed length
    i = 0
    shift = 0
    ulen = 0
    while i < len(src):
        b = src[i]
        i += 1
        ulen |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    out = bytearray()
    while i < len(src) and len(out) < limit:
        tag = src[i]
        t = tag & 3
        if t == 0:
            ln = tag >> 2
            if ln < 60:
                i += 1
                ln += 1
            else:
                nb = ln - 59
                i += 1
                ln = int.from_bytes(src[i:i + nb], "little") + 1
                i += nb
            out += src[i:i + ln]
            i += ln
        else:
            if t == 1:
                ln = ((tag >> 2) & 7) + 4
                off = ((tag >> 5) << 8) | src[i + 1]
                i += 2
            elif t == 2:
                ln = (tag >> 2) + 1
                off = int.from_bytes(src[i + 1:i + 3], "little")
                i += 3
            else:
                ln = (tag >> 2) + 1
                off = int.from_bytes(src[i + 1:i + 5], "little")
                i += 5
            if off == 0 or off > len(out):
                return bytes(out), "bad-offset"
            for _ in range(ln):
                out.append(out[-off])
    return bytes(out), f"ok(ulen={ulen})"


def main():
    p = sys.argv[1]
    ent, blk = load(p)
    e = ent[0]
    w = max(e[6], e[7])
    h = min(e[6], e[7])
    print(f"{p}\n entry0={e} w*h*3={w*h*3} blk={len(blk)}")
    for start in range(0, 8):
        out, st = lz4_decode(blk, start)
        print(f"  LZ4 start={start}: {len(out)} ({st})")
    out, st = snappy_decode(blk)
    print(f"  Snappy: {len(out)} ({st})")


if __name__ == "__main__":
    main()
