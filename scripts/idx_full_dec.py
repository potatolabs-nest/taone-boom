#!/usr/bin/env python3
"""Decode a whole big `ca da ef` .idx as ONE continuous XOR-chain stream.

plain[i] = raw[i] ^ plain[i-4]   (i >= 4);   plain[0:4] = raw[0:4] ^ seed

The chain runs over the file, so a single 4-byte seed decodes everything;
records are the NUL-terminated strings inside that plaintext.

Usage: python3 -I idx_full_dec.py <idx> [--seed 0f000000] [--dump N]
"""
import argparse, os, struct, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
EXTS = (b".bmp", b".dds", b".ogg", b".ani", b".scr", b".tga", b".jpg", b".jpeg",
        b".png", b".luc", b".txt", b".ini", b".xml", b".wav", b".bik", b".cur",
        b".slk", b".fft", b".dat", b".mp3", b".spr", b".img", b".act", b".eff")


def decode(raw, seed):
    n = len(raw)
    out = bytearray(n)
    s = seed
    # first 4
    for i in range(min(4, n)):
        out[i] = raw[i] ^ s[i]
    for i in range(4, n):
        out[i] = raw[i] ^ out[i - 4]
    return out


def score(pt, start):
    """Count long printable runs and known extensions."""
    runs = []
    i = start
    n = len(pt)
    while i < n:
        if pt[i] in PATHCH:
            j = i
            while j < n and pt[j] in PATHCH:
                j += 1
            if j - i >= 8:
                runs.append((i, pt[i:j]))
            i = j
        else:
            i += 1
    ext = sum(1 for _, r in runs if r.lower().endswith(EXTS))
    return runs, ext


def best_seed(raw):
    best = None
    for k in range(256):
        for k2 in (0,):       # seed[1:4] hit 0 on every archive checked
            seed = bytes([k, k2, k2, k2])
            pt = decode(raw, seed)
            runs, ext = score(pt, 16)
            sc = (len(runs) + 10 * ext, ext, len(runs))
            if best is None or sc > best[0]:
                best = (sc, seed, runs)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idx")
    ap.add_argument("--seed")
    ap.add_argument("--dump", type=int, default=0)
    args = ap.parse_args()

    raw = open(args.idx, "rb").read()
    print(f"{os.path.basename(args.idx)} size={len(raw):,}")
    if args.seed:
        seed = bytes.fromhex(args.seed)
        pt = decode(raw, seed)
        runs, ext = score(pt, 16)
        print(f"seed={seed.hex(' ')} runs={len(runs)} ext={ext}")
    else:
        sc, seed, runs = best_seed(raw)
        pt = decode(raw, seed)
        print(f"best seed={seed.hex(' ')} score={sc}")

    print(f"--- {len(runs)} printable runs (>=8 chars), first 25 ---")
    for off, r in runs[:25]:
        tag = "EXT" if r.lower().endswith(EXTS) else "   "
        print(f"  @{off:#08x} {tag} {r.decode('latin1')!r}")

    if args.dump:
        print(f"--- plaintext hexdump from 0x10, {args.dump} bytes ---")
        d = pt[16:16 + args.dump]
        for i in range(0, len(d), 16):
            chunk = d[i:i + 16]
            asc = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
            print(f"  {16+i:#08x}: {chunk.hex(' '):<47} {asc}")


if __name__ == "__main__":
    main()
