#!/usr/bin/env python3
"""Decode the whole body of a big `ca da ef` .idx with one global XOR chain.

plain[i] = raw[i] ^ plain[i-4]  (i >= 4)  from the record-0 head offset.
Seed from the head's directory prefix (Game/ etc).

Usage: python3 -I idx_glob.py <idx> <prefix> [--off 0x10] [--dump N] [--breakat]
"""
import argparse, os, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")


def decode(raw, off, prefix):
    n = len(raw)
    seed = bytes(raw[off + i] ^ prefix[i] for i in range(4))
    m = n - off
    out = bytearray(m)
    for i in range(min(4, m)):
        out[i] = raw[off + i] ^ seed[i]
    for i in range(4, m):
        out[i] = raw[off + i] ^ out[i - 4]
    return bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idx")
    ap.add_argument("prefix")
    ap.add_argument("--off", type=lambda s: int(s, 0), default=0x10)
    ap.add_argument("--dump", type=int, default=512)
    args = ap.parse_args()

    raw = open(args.idx, "rb").read()
    pt = decode(raw, args.off, args.prefix.encode())
    print(f"{os.path.basename(args.idx)} size={len(raw):,} off={args.off:#x} prefix={args.prefix}")
    d = pt[:args.dump]
    for i in range(0, len(d), 16):
        ch = d[i:i + 16]
        asc = "".join(chr(c) if 32 <= c < 127 else "." for c in ch)
        print(f"  {args.off+i:#08x}: {ch.hex(' '):<47} {asc}")


if __name__ == "__main__":
    main()
