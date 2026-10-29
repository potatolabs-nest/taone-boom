#!/usr/bin/env python3
"""Test length-prefixed chunk framings on a .table payload, using the Monster2
record whose artwork is also present as a plaintext BMP.
"""
import struct
import sys
import zlib
from collections import Counter


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def load(p):
    b = open(p, "rb").read()
    if len(b) > 8 and u32(b, 0) == len(b) - 8:
        b = zlib.decompress(b[8:])
    c = u32(b, 0)
    hdr = 24 + 48 * c
    blk = b[hdr:]
    if u32(blk, 0) == len(blk) - 4:
        blk = blk[4:]
    return blk


def chunks(buf, hsz, little=True, limit=1 << 22):
    out = bytearray()
    i = 0
    n = len(buf)
    nch = 0
    while i + hsz <= n:
        ln = int.from_bytes(buf[i:i + hsz], "little" if little else "big")
        i += hsz
        if ln == 0:
            nch += 1
            if out:
                pass
            continue
        if ln > n - i:
            return bytes(out), nch, f"overrun at {i} (len {ln} > {n-i})"
        out += buf[i:i + ln]
        i += ln
        nch += 1
        if len(out) > limit:
            return bytes(out), nch, "limit"
    return bytes(out), nch, f"clean end at {i}/{n}"


def main():
    blk = load(sys.argv[1])
    print(f"block={len(blk)}")
    for hsz in (1, 2, 4):
        for start in range(0, 6):
            o, nch, st = chunks(blk[start:], hsz)
            print(f"  hsz={hsz} start={start}: {len(o)} bytes, {nch} chunks, {st}")
    # alternative: [len][data] where len is a single byte and high bit = literal
    for start in range(0, 4):
        out, st = chunks_alt(blk, start)
        print(f"  alt(start={start}): {len(out)} ({st})")


def chunks_alt(buf, start):
    out = bytearray()
    i = start
    n = len(buf)
    while i < n:
        c = buf[i]
        i += 1
        ln = c & 0x7F
        if ln == 0:
            continue
        out += buf[i:i + ln]
        i += ln
        if len(out) > 1 << 22:
            return bytes(out), "limit"
    return bytes(out), f"end {i}/{n}"


if __name__ == "__main__":
    main()
