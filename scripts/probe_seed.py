#!/usr/bin/env python3
"""Recover the 4-byte seed (assumed (k,0,0,0)) for each big idx by brute force.

The seed derivation dec[0:4] = prefix is circular, so the prefix cannot be
read off the bytes; the only real signal is whether dec[4:] forms a valid path.
"""
import struct, sys, os, glob

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
EXTS = (b".bmp", b".dds", b".ogg", b".ani", b".scr", b".tga", b".jpg", b".jpeg",
        b".png", b".luc", b".txt", b".ini", b".xml", b".wav", b".bik", b".cur")


def decrypt_seed(stem, seed):
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def score(nm):
    """Leading printable path-char run length; must contain a '/' segment."""
    if len(nm) < 6 or b"/" not in nm:
        return 0
    return len(nm)


def run(o):
    L = 0
    while L < len(o) and o[L] in PATHCH:
        L += 1
    return o[:L]


def best_k(idx, off=16, window=64):
    res = []
    for k in range(256):
        seed = bytes([k, 0, 0, 0])
        o = decrypt_seed(idx[off:off + window], seed)
        s = score(run(o))
        if s:
            res.append((s, k, run(o)))
    res.sort(reverse=True)
    return res


def main():
    BOOM = "extracted/Boom"
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(BOOM, "*.idx")))
    for path in files:
        idx = open(path, "rb").read()
        if idx[:3] != b"\xca\xda\xef" and idx[:3] != b"0\xab\x9c":
            continue
        res = best_k(idx)
        nm = os.path.basename(path)
        if res:
            print(f"{nm:18s} k={res[0][1]:#04x} -> {res[0][2].decode('latin1')!r}  ({len(res)} k's valid)")
            for s, k, v in res[:4]:
                print(f"      k={k:#04x} len={s} {v.decode('latin1')!r}")
        else:
            print(f"{nm:18s} no valid k at offset 16")


if __name__ == "__main__":
    main()
