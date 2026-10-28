#!/usr/bin/env python3
"""Annotate the exact byte layout of the first N records of a big idx."""
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


def main():
    idx = open(sys.argv[1], "rb").read()
    prefix = sys.argv[2].encode() if len(sys.argv) > 2 else b"Game/"
    nrec = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    p = 16
    L = scan_len(idx, p, prefix)
    for i in range(nrec):
        name = decrypt(idx[p:p + L], prefix)
        print(f"=== rec {i}  head@{p:#06x}  name_len={L}")
        print(f"    head raw ({L:2d}B): {idx[p:p+L].hex(' ')}")
        print(f"    head dec        : {name.decode('latin1')!r}")
        # print the next 32 bytes raw with 4-byte grouping
        tail = idx[p + L:p + L + 32]
        print(f"    after raw       : {tail.hex(' ')}")
        for k in range(8):
            v = u32(idx, p + L + 4 * k)
            asc = "".join(chr(c) if 32 <= c < 127 else "." for c in v.to_bytes(4, "little"))
            print(f"      u32 @{p+L+4*k:#06x} = {v:12d} ({v:#010x}) {asc!r}")
        nxt = u32(idx, p + L + 16)
        print(f"    -> next head len {nxt}; next record at {p+L+20:#06x} (if 20B trailer)")
        if nxt < 4 or nxt > 500:
            print("    chain broken")
            break
        p = p + L + 20
        L = nxt
        if p + L + 20 > len(idx):
            print("    out of range")
            break


if __name__ == "__main__":
    main()
