#!/usr/bin/env python3
"""Decode the body of a big `ca da ef` .idx as one global XOR chain.

plain[0x10:0x14] = first 4 chars of the first name (usually a directory).
plain[i] = raw[i] ^ plain[i-4]  for i >= 0x14.

seed = raw[0x10:0x14] ^ first4name. Since chars 2..4 of the first path are
plaintext, seed = (k,0,0,0) and k is brute-forced with a whole-body score.

Usage: python3 -I idx_body.py <idx> [--k 0x17] [--dump N] [--runs]
"""
import argparse, os, struct, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
EXTS = (b".bmp", b".dds", b".ogg", b".ani", b".scr", b".tga", b".jpg", b".jpeg",
        b".png", b".luc", b".txt", b".ini", b".xml", b".wav", b".bik", b".cur",
        b".slk", b".fft", b".dat", b".mp3", b".spr", b".img", b".act", b".eff")


def body(raw, k):
    n = len(raw)
    if n <= 0x14:
        return b""
    out = bytearray(n - 0x10)
    src = raw[0x10:]
    out[0] = src[0] ^ k
    out[1] = src[1]
    out[2] = src[2]
    out[3] = src[3]
    for i in range(4, len(src)):
        out[i] = src[i] ^ out[i - 4]
    return bytes(out)


def score(buf):
    """printable-ASCII fraction + bonus for known extensions + NUL count."""
    if not buf:
        return (0, 0, 0)
    pr = 0
    nz = 0
    for c in buf:
        if 32 <= c < 127 or c in PATHCH:
            pr += 1
        if c == 0:
            nz += 1
    ext = 0
    for e in EXTS:
        ext += buf.count(e)
    # names carry a dot; count '.' too
    return (pr / len(buf) + 0.05 * ext, ext, nz)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idx")
    ap.add_argument("--k", type=lambda s: int(s, 0))
    ap.add_argument("--dump", type=int, default=0)
    ap.add_argument("--runs", action="store_true")
    ap.add_argument("--scan", type=int, default=0, help="print first N records via NUL-split")
    args = ap.parse_args()

    raw = open(args.idx, "rb").read()
    print(f"{os.path.basename(args.idx)} size={len(raw):,}")
    if args.k is None:
        best = None
        for k in range(256):
            sc = score(body(raw, k))
            if best is None or sc > best[0]:
                best = (sc, k)
        k = best[1]
        print(f"best k={k:#04x} score={best[0]}")
    else:
        k = args.k
    pt = body(raw, k)
    if args.k is None:
        print(f"first name => {pt[:3].decode('latin1')!r} seed hex={bytes([raw[0x10]^pt[0],0,0,0]).hex(' ')}")
    print(f"  first 64: {pt[:64].decode('latin1','replace')!r}")

    if args.dump:
        d = pt[:args.dump]
        for i in range(0, len(d), 16):
            ch = d[i:i + 16]
            asc = "".join(chr(c) if 32 <= c < 127 else "." for c in ch)
            print(f"  {0x10+i:#08x}: {ch.hex(' '):<47} {asc}")

    if args.runs:
        print("--- printable runs >= 8 ---")
        i, n = 0, len(pt)
        cnt = 0
        while i < n and cnt < 40:
            if pt[i] in PATHCH:
                j = i
                while j < n and pt[j] in PATHCH:
                    j += 1
                if j - i >= 8:
                    tag = "EXT" if pt[i:j].lower().endswith(EXTS) else "   "
                    print(f"  @{0x10+i:#08x} {tag} {pt[i:j].decode('latin1')!r}")
                    cnt += 1
                i = j
            else:
                i += 1


if __name__ == "__main__":
    main()
