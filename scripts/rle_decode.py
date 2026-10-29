#!/usr/bin/env python3
"""Decode the BGR run-length stream found in `.table` blocks.

`FxStage/00561_Lobby__Monster2_bt01.table` holds the same artwork as the
plaintext BMP `extracted/Boom/vh/Lobby_Monster2_bt01.bmp` (171x880 24bpp), so
this record is a decoder ground truth.  The block is a stream of
`[count][B][G][R]` runs plus a variable-length prefix; we test whether a decode
reproduces exactly w*h pixels.
"""
import struct
import sys
import zlib

sys.path.insert(0, "/Users/hieu/Workspaces/taone/scripts")
import pngwrite  # noqa: E402


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


def dec_runs(body, start, count_fmt):
    """Token = [count byte][B][G][R]. count_fmt: 'raw' (1..255) or 'flag7'."""
    out = bytearray()
    i = start
    n = len(body)
    while i + 3 < n:
        c = body[i]
        if count_fmt == "flag7" and c >= 0x80:
            cnt = c & 0x7F
        else:
            cnt = c
        if cnt == 0:
            i += 1
            continue
        bgr = body[i + 1:i + 4]
        out += bytes(bgr) * cnt
        i += 4
    return out


def main():
    tp = sys.argv[1]
    ent, blk = load(tp)
    e = ent[0]
    w = max(e[6], e[7])
    h = min(e[6], e[7])
    print(f"{tp}\n entry0={e} w={w} h={h} block={len(blk)} pixels={w*h} "
          f"ratio={len(blk)/(w*h):.4f}")
    # token census from offset 0 assuming [count][bgr] from various starts
    for start in range(0, 40):
        body = blk
        out = dec_runs(body, start, "raw")
        if len(out) >= w * h:
            print(f"  start={start} raw-count -> {len(out)} px (>= {w*h})")
            break
    # count tokens / runaway
    out = dec_runs(blk, 0, "raw")
    print(f"  raw from 0 -> {len(out)} px")
    # distribution of token count bytes
    from collections import Counter
    cnts = Counter()
    for i in range(0, min(len(blk) - 4, 40000), 4):
        cnts[blk[i]] += 1
    print(f"  token count-byte histogram (offset 0 mod4): {cnts.most_common(10)}")


if __name__ == "__main__":
    main()
