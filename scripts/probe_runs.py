#!/usr/bin/env python3
"""Probe: find maximal printable 'Game/...' name runs in a big Fx*.idx.

No record walk assumed. For every byte offset we derive the seed from a given
directory prefix and decrypt forward, then measure the printable path-char run.
"""
import sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")


def runs(idx, prefix=b"Game/", minlen=8):
    pfx = prefix
    n = len(idx)
    out = []
    for p in range(16, n - 8):
        seed = bytes(idx[p + i] ^ pfx[i] for i in range(4))
        # decrypt a window
        buf = bytearray()
        for i in range(min(160, n - p)):
            b = idx[p + i]
            buf.append(b ^ (seed[i] if i < 4 else buf[i - 4]))
        # printable run
        L = 0
        for b in buf:
            if b in PATHCH:
                L += 1
            else:
                break
        if L >= minlen:
            out.append((p, L, bytes(buf[:L]).decode("latin1")))
    return out


def main():
    path = sys.argv[1]
    idx = open(path, "rb").read()
    rs = runs(idx)
    print(f"{path}: {len(rs)} candidate starts")
    # print first 60
    for p, L, s in rs[:80]:
        print(f"  {p:#08x} len={L:3d} {s}")
    # distribution of lengths
    from collections import Counter
    print("len histogram:", sorted(Counter(L for _, L, _ in rs).items())[:40])


if __name__ == "__main__":
    main()
