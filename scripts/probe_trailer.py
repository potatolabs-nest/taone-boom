#!/usr/bin/env python3
"""Examine trailer field semantics across the whole chain."""
import struct, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")


def decrypt(stem, prefix):
    seed = bytes(stem[i] ^ prefix[i] for i in range(4))
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def scan_len(idx, p, prefix, cap=512):
    o = decrypt(idx[p:p + cap], prefix)
    L = 0
    while L < len(o) and o[L] in PATHCH:
        L += 1
    return L


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def walk(idx, prefix):
    n = len(idx)
    p = 16
    L = scan_len(idx, p, prefix)
    recs = []
    while L >= 4 and p + L + 20 <= n:
        recs.append((p, L, decrypt(idx[p:p + L], prefix)))
        nxt = u32(idx, p + L + 16)
        p = p + L + 20
        L = nxt
    return recs


def main():
    idx = open(sys.argv[1], "rb").read()
    prefix = sys.argv[2].encode() if len(sys.argv) > 2 else b"Game/"
    recs = walk(idx, prefix)
    print(f"{len(recs)} records, last end {recs[-1][0]+recs[-1][1]+20:#x} / file {len(idx):#x}")
    printable0 = 0
    for i, (p, L, nm) in enumerate(recs[:25]):
        t = [u32(idx, p + L + 4 * k) for k in range(5)]
        asc = "".join(chr(c) if 32 <= c < 127 else "." for c in t[0].to_bytes(4, "little"))
        print(f"{i:3d} L={L:3d} name={nm.decode('latin1'):32s} t0={t[0]:#010x} '{asc}' t1={t[1]:8d} t2={t[2]:8d} t3={t[3]} next={t[4]}")
    # how many trailer0 are all-printable
    for p, L, nm in recs:
        v = u32(idx, p + L)
        s = v.to_bytes(4, "little")
        if all(32 <= c < 127 for c in s):
            printable0 += 1
    print(f"\ntrailer0 printable-ascii in {printable0}/{len(recs)} records")
    # statistics on t1,t2,t3
    import collections
    c3 = collections.Counter(u32(idx, p + L + 12) for p, L, nm in recs)
    print("t3 values:", c3.most_common(5))
    # monotonicity of t1/t2
    t1 = [u32(idx, p + L + 4) for p, L, nm in recs]
    inc = all(t1[i] <= t1[i + 1] for i in range(len(t1) - 1))
    print("t1 monotonic non-decreasing:", inc)
    print("t1 first/last:", t1[0], t1[-1], " t2 last:", u32(idx, recs[-1][0] + recs[-1][1] + 8))


if __name__ == "__main__":
    main()
