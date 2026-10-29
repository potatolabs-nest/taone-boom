#!/usr/bin/env python3
"""Walk records of the big `ca da ef` .idx family.

Cipher (NOTES.md section 8, generalised):  plain[i] = raw[i] ^ plain[i-4].
Because the recurrence has lag 4, the four residue classes mod 4 are
independent XOR chains, each with one unknown constant (one seed byte). Each
seed byte is solved independently by requiring the chain to stay printable --
no directory prefix needs to be guessed.

Record hypothesis H1 (tested here):
    record(p) = [name: L bytes][0x00][meta: 16 bytes = 4 u32]
    meta[12:16] = L of the NEXT record; next p = p + L + 1 + 16
    first record's L is recovered from the decode (printed run length).

Usage: python3 -I idd_rec.py <idx> [--recs N] [--hex]
"""
import argparse, os, struct, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
EXTS = (b".bmp", b".dds", b".ogg", b".ani", b".scr", b".tga", b".jpg", b".jpeg",
        b".png", b".luc", b".txt", b".ini", b".xml", b".wav", b".bik", b".cur",
        b".slk", b".fft", b".dat", b".mp3", b".spr", b".img", b".act", b".eff",
        b".plist", b".tiff", b".pcx", b".gif")


def solve_seed(raw, p, cap):
    """Solve the 4 seed bytes; return (seed, plaintext_bytes)."""
    m = min(cap, len(raw) - p)
    if m < 8:
        return None, None
    stem = raw[p:p + m]
    seed = [0] * 4
    for j in range(4):
        # chain j: values x_t = seed[j] ^ XOR_{s} stem[j+4s] for s<t
        acc = []
        k = j
        x = 0
        while k < m:
            x ^= stem[k]
            acc.append((k, x))
            k += 4
        best = None
        for s in range(256):
            good = 0
            for (kk, xv) in acc:
                c = s ^ xv
                if c in PATHCH:
                    good += 1
                elif c == 0:
                    good += 1        # NUL terminator also fine
                    break
                else:
                    break
            else:
                pass
            if best is None or good > best[0]:
                best = (good, s)
        seed[j] = best[1]
    out = bytearray(m)
    for i in range(m):
        out[i] = raw[p + i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(seed), bytes(out)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idx")
    ap.add_argument("--recs", type=int, default=12)
    ap.add_argument("--hex", action="store_true")
    args = ap.parse_args()

    raw = open(args.idx, "rb").read()
    n = len(raw)
    print(f"{os.path.basename(args.idx)}  size={n:,}  magic={raw[:4].hex(' ')}")
    print(f"  hdr u32: {[u32(raw, 4*k) for k in range(4)]}")
    p = 16
    for k in range(args.recs):
        if p + 40 > n:
            print("  EOF")
            break
        seed, pt = solve_seed(raw, p, 8192)
        L = 0
        while L < len(pt) and pt[L] in PATHCH:
            L += 1
        name = pt[:L]
        if args.hex:
            print(f"  raw @{p:#08x}: {raw[p:p+L+24].hex(' ')}")
        print(f"  rec{k:3d} @{p:#08x} seed={seed.hex(' ')} L={L}")
        print(f"        name: {name.decode('latin1')}")
        term = pt.find(b"\x00")
        if term < 0 or term != L:
            print(f"        !! no NUL right after name (first NUL at {term})")
            break
        mo = L + 1
        vals = [u32(pt, mo + 4 * j) for j in range(4)]
        print(f"        meta: a={vals[0]:,} b={vals[1]:,} c={vals[2]:,} Lnext={vals[3]}")
        if not (4 <= vals[3] <= 4096):
            print("        chain broken (Lnext out of range)")
            break
        p = p + L + 1 + 16


if __name__ == "__main__":
    main()
