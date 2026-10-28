#!/usr/bin/env python3
"""Discover the big Fx*.idx record layout by chaining hypotheses.

Record: [u32 head_len][head (obfuscated name, head_len bytes)]
        [u16 name_len][name (plaintext, name_len bytes)]
        [20-byte trailer: A,B,C,0,next_head_len]
so next record starts at p + head_len + 2 + name_len + 20.
"""
import struct, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
EXTS = (b".bmp", b".dds", b".ogg", b".ani", b".scr", b".tga", b".jpg", b".jpeg",
        b".png", b".luc", b".txt", b".ini", b".xml", b".wav", b".bik", b".cur")


def decrypt(stem, prefix):
    seed = bytes(stem[i] ^ prefix[i] for i in range(4))
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def valid(nm, prefix=b"Game/"):
    if len(nm) < 8:
        return False
    if any(b not in PATHCH for b in nm):
        return False
    if not nm.startswith(prefix):
        return False
    if not nm.lower().endswith(EXTS):
        return False
    if b"//" in nm or b"/." in nm:
        return False
    return True


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def walk(idx, start=16, prefix=b"Game/", limit=None):
    n = len(idx)
    p = start
    recs = []
    while p + 4 <= n:
        L = u32(idx, p)
        if not (4 <= L <= 500) or p + 4 + L + 2 > n:
            break
        nl = u16(idx, p + 4 + L)
        if not (1 <= nl <= 300) or p + 4 + L + 2 + nl + 20 > n:
            break
        nm = decrypt(idx[p + 4:p + 4 + L], prefix)
        raw = idx[p + 4 + L + 2:p + 4 + L + 2 + nl]
        recs.append((p, L, nl, nm, raw))
        p = p + 4 + L + 2 + nl + 20
        if limit and len(recs) >= limit:
            break
    return recs


def main():
    idx = open(sys.argv[1], "rb").read()
    prefix = sys.argv[2].encode() if len(sys.argv) > 2 else b"Game/"
    recs = walk(idx, prefix=prefix, limit=25)
    for p, L, nl, nm, raw in recs:
        nmv = nm.decode("latin1")
        rawv = raw.decode("latin1")
        print(f"p={p:#08x} L={L:3d} nl={nl:3d}")
        print(f"   head-> {nmv}")
        print(f"   raw  -> {rawv!r}")


if __name__ == "__main__":
    main()
