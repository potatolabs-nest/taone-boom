#!/usr/bin/env python3
"""Find which directory prefix each big idx uses for its record names."""
import os, glob, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
DIRS = [b"Game/", b"Character/", b"AIBattle/", b"Monster/", b"Sound/", b"Map/",
        b"Contents/", b"Desktop/", b"HiddenCatch/", b"Fx/", b"Effect/",
        b"Quest/", b"PopupEvent/", b"Stage/", b"Item/", b"Ui/", b"UI/",
        b"Interface/", b"Loading/", b"Data/", b"Image/", b"Texture/",
        b"Avatar/", b"Pet/", b"Npc/", b"Event/", b"Bg/", b"Bg/", b"Common/",
        b"Back/", b"Cash/", b"Latale/", b"Rhythm/", b"Dance/", b"Mode/"]


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
        nm = os.path.basename(path)
        found = []
        for pfx in [d for d in DIRS if len(d) >= 4]:
            o = dec(idx[16:16 + 96], pfx)
            if o[:len(pfx)] != pfx:
                continue
            L = runlen(o)
            if L >= len(pfx) + 6:
                found.append((L, pfx, o[:L]))
        found.sort(reverse=True)
        print(f"{nm:18s} " + "; ".join(f"{p.decode()}(len{L}) -> {v.decode('latin1')!r}" for L, p, v in found[:3]) or f"{nm}: none")


if __name__ == "__main__":
    main()
