#!/usr/bin/env python3
"""Find every [u16 len][ascii tail] pair in a big idx, to locate record anchors."""
import struct, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")


def main():
    idx = open(sys.argv[1], "rb").read()
    n = len(idx)
    out = []
    for p in range(16, n - 3):
        L = struct.unpack_from("<H", idx, p)[0]
        if not (1 <= L <= 96):
            continue
        t = idx[p + 2:p + 2 + L]
        if len(t) < L:
            continue
        if all(c in PATHCH for c in t):
            out.append((p, L, t))
    print(f"{len(out)} [u16][ascii] pairs")
    prev = None
    for p, L, t in out[:40]:
        gap = "" if prev is None else f" gap={p-prev:d}"
        # show the 24 bytes before p
        print(f"  @{p:#07x} L={L:2d} {t.decode('latin1')!r}{gap}  pre={idx[max(0,p-24):p].hex(' ')}")
        prev = p
    # tail-length histogram
    from collections import Counter
    print("\nL histogram:", Counter(L for _, L, _ in out).most_common(20))


if __name__ == "__main__":
    main()
