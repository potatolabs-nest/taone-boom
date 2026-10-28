#!/usr/bin/env python3
"""Find genuine obfuscated name heads and dump their full record anatomy.

A genuine head is a position p where decrypt(p, "Game/") yields
"Game/" + path chars + a known extension, immediately followed by a byte that
is NOT a path char (NUL padding or a low control byte).
"""
import struct, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
EXTS = (b".bmp", b".dds", b".ogg", b".ani", b".scr", b".tga", b".jpg", b".jpeg",
        b".png", b".luc", b".txt", b".ini", b".xml", b".wav", b".bik", b".cur",
        b".slk", b".fft")


def decrypt(stem, prefix):
    seed = bytes(stem[i] ^ prefix[i] for i in range(4))
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def head_at(idx, p, prefix=b"Game/", window=512):
    """Return (name, name_len) if a genuine name head starts at p, else None."""
    if p + 4 > len(idx):
        return None
    w = idx[p:p + window]
    if len(w) < 12:
        return None
    o = decrypt(w, prefix)
    L = 0
    while L < len(o) and o[L] in PATHCH:
        L += 1
    if L < 10:
        return None
    nm = o[:L]
    if not nm.startswith(prefix) or not nm.lower().endswith(EXTS):
        return None
    # must be terminated by a non path char
    if L < len(o) and o[L] in PATHCH:
        return None
    return nm, L


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def main():
    idx = open(sys.argv[1], "rb").read()
    prefix = sys.argv[2].encode() if len(sys.argv) > 2 else b"Game/"
    n = len(idx)
    heads = []
    p = 16
    while p + 16 < n:
        r = head_at(idx, p, prefix)
        if r:
            heads.append((p, r[0], r[1]))
            p += 1
        else:
            p += 1
    print(f"{len(heads)} genuine heads")
    for i, (p, nm, nl) in enumerate(heads[:int(sys.argv[3]) if len(sys.argv) > 3 else 12]):
        # dump 48 bytes of the record from p
        print(f"--- rec {i}: head@{p:#08x} name_len={nl}")
        print(f"    name={nm.decode('latin1')}")
        print(f"    u32@p-4={u32(idx,p-4)} (0x{u32(idx,p-4):x})")
        nxt = p + 16 if i == 0 else heads[i][0]
        # show raw head bytes
        print(f"    head raw: {idx[p:p+nl+8].hex(' ')}")
        # after name
        a = [u32(idx, p + nl + 4 * k) for k in range(6)]
        print(f"    after name: u32s = {[hex(x) for x in a]}")
        print(f"    raw after: {idx[p+nl:p+nl+28].hex(' ')}")
    # spacing
    print("\nspacings between consecutive heads:")
    for i in range(1, min(len(heads), 30)):
        print(f"  {heads[i][0]-heads[i-1][0]:5d}  {heads[i-1][1].decode('latin1')[:40]}")


if __name__ == "__main__":
    main()
