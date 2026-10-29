#!/usr/bin/env python3
"""Crack the T3 sprite payload codec using known ground truth.

Ground truth: extracted/Boom/vh/*.bmp are plaintext 24bpp BMPs whose names
match .table records one-for-one. So a candidate decoder can be SCORED against
the real image instead of eyeballed.

Reasoning that drives the search:
  - payload is ~3.2 bytes/pixel
  - raw RGB is 3.0, raw RGBA is 4.0
  - so the source is most likely 32-bit RGBA under a ~80% codec, not 24-bit RGB
    under an expanding one
  - a 189-byte verbatim run exists inside an otherwise 98.5%-different stream,
    which is the signature of LZ77/LZSS: literals pass through unchanged

Usage: python3 -I crack_t3_sprite.py [--time-budget SECONDS]
"""
import argparse, math, os, struct, sys, time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BMP = os.path.join(ROOT, "extracted/Boom/vh/Lobby_Monster2_bt01.bmp")
TBL = os.path.join(ROOT, "work/assets/by_index/FxStage/00561_Lobby__Monster2_bt01.table")


def load_pair():
    t = open(TBL, "rb").read()
    cnt, f2, h2, h3, wm, hm = struct.unpack_from("<6I", t, 0)
    hlen = 24 + 48 * cnt
    pay = t[hlen:]
    b = open(BMP, "rb").read()
    off = struct.unpack_from("<I", b, 10)[0]
    w, h = struct.unpack_from("<ii", b, 18)
    px = b[off:]
    # BMP is bottom-up; convert to top-down RGB triples
    rows = [px[y * w * 3:(y + 1) * w * 3] for y in range(h)]
    flat = b"".join(reversed(rows))
    return pay, flat, w, h


def hist(b):
    return Counter(b)


def cos(a, c):
    keys = set(a) | set(c)
    na = math.sqrt(sum(v * v for v in a.values())) or 1
    nc = math.sqrt(sum(v * v for v in c.values())) or 1
    return sum(a.get(k, 0) * c.get(k, 0) for k in keys) / (na * nc)


# ---------------- candidate LZSS variants ----------------
def lzss_flagbits(src, out_cap, lit_is_one=True, off_bits=12, len_bits=4,
                  min_len=3, window=4096, max_len=None):
    """flag byte then 8 items; item = literal(1B) or (offset,length)."""
    out = bytearray()
    i = 0
    n = len(src)
    if max_len is None:
        max_len = (1 << len_bits) + min_len - 1
    len_mask = (1 << len_bits) - 1
    off_mask = (1 << off_bits) - 1
    while i < n and len(out) < out_cap:
        flags = src[i]; i += 1
        for bit in range(8):
            if i >= n or len(out) >= out_cap:
                break
            islit = ((flags >> bit) & 1) == (1 if lit_is_one else 0)
            if islit:
                out.append(src[i]); i += 1
            else:
                if i + 2 > n:
                    i = n
                    break
                v = src[i] | (src[i + 1] << 8); i += 2
                off = (v >> len_bits) & off_mask
                ln = (v & len_mask) + min_len
                if off == 0 or off > len(out):
                    # invalid back-reference: bail on this candidate
                    return bytes(out), False
                start = len(out) - off
                for k in range(ln):
                    if len(out) >= out_cap:
                        break
                    out.append(out[start + k])
    return bytes(out), True


def score(decoded, flat, w, h):
    """Compare decoded RGBA (4B/px) to the 24bpp BMP ground truth."""
    px = len(flat) // 3
    if len(decoded) < px * 3:
        return -1.0
    # take every 4th-byte-aligned triple, drop alpha
    rgb = bytearray()
    for k in range(px):
        o = k * 4
        rgb += decoded[o:o + 3]
    return cos(hist(bytes(rgb)), hist(flat))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time-budget", type=float, default=90)
    args = ap.parse_args()

    pay, flat, w, h = load_pair()
    cap = w * h * 4
    print(f"payload={len(pay):,}  bmp={len(flat):,}  target RGBA={cap:,}  {w}x{h}")
    print(f"payload/px = {len(pay)/(w*h):.3f}   (RGB=3.0, RGBA=4.0)")

    t0 = time.time()
    best = []
    tried = 0
    for lit in (True, False):
        for off_bits in (8, 10, 11, 12, 13, 14, 15, 16):
            for len_bits in (4, 5, 6, 8):
                for min_len in (2, 3, 4):
                    if time.time() - t0 > args.time_budget:
                        print("time budget reached")
                        break
                    tried += 1
                    dec, ok = lzss_flagbits(pay, cap, lit, off_bits, len_bits, min_len)
                    if not ok or len(dec) < cap * 0.9:
                        continue
                    s = score(dec, flat, w, h)
                    best.append((s, lit, off_bits, len_bits, min_len, len(dec)))
    best.sort(reverse=True)
    print(f"\ntried {tried} variants in {time.time()-t0:.1f}s")
    print("top scorers (higher is better; ~0.01 = noise, ~0.77 = real match):")
    for s, lit, ob, lb, ml, ln in best[:12]:
        print(f"   score={s:.4f}  literal_is_1={lit} off_bits={ob} len_bits={lb} "
              f"min_len={ml} out={ln:,}")


if __name__ == "__main__":
    main()
