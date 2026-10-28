#!/usr/bin/env python3
"""For each big idx, find offsets where decrypting with a candidate prefix
yields a long printable path-like run. Tells us the real prefix per archive."""
import sys, os, glob, struct

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
PFX = [b"Game/", b"Quest/", b"PopupEvent/"]


def dec(stem, pfx):
    seed = bytes(stem[i] ^ pfx[i] for i in range(4))
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def runlen(o):
    L = 0
    while L < len(o) and o[L] in PATHCH:
        L += 1
    return L


def main():
    for path in sorted(glob.glob("extracted/Boom/*.idx")):
        idx = open(path, "rb").read()
        if idx[:3] != b"\xca\xda\xef":
            continue
        best = (0, None, None, None)
        for pfx in PFX:
            for p in range(16, min(len(idx), 3000)):
                o = dec(idx[p:p + 64], pfx)
                L = runlen(o)
                if o[:len(pfx)] != pfx:
                    continue
                if L > best[0]:
                    best = (L, pfx, p, o[:L])
        nm = os.path.basename(path)
        if best[0] >= 10:
            print(f"{nm:18s} best run={best[0]:3d} pfx={best[1]} @{best[2]:#06x} {best[3].decode('latin1')!r}")
        else:
            print(f"{nm:18s} NO clean run (best {best[0]})")


if __name__ == "__main__":
    main()
