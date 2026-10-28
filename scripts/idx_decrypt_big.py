#!/usr/bin/env python3
"""Decode the big `Fx*.idx` family (magic `ca da ef XX`).

LAYOUT (confirmed):

  u32 magic ('ca da ef XX') | u32 version=15 | u32 count_a | u32 count_b
  then, from offset 0x10, a chain of records:

      record = [ head  : L bytes, obfuscated name ]
               [ meta  : 16 bytes = four u32 ]
               [ u32 Lnext ]            <- head length of the NEXT record

  so next record starts at p + L + 20. Only the first record's L is not
  written down; it is recovered from the decrypted run.

CIPHER (already known, reused): name[i] = stem[i] ^ name[i-4], with
name[0:4] = stem[0:4] ^ seed. For this family the seed is (k, 0, 0, 0), i.e.
name[1:4] == stem[1:4] verbatim and only name[0] is masked by k. k is derived
from the archive's directory prefix (name[0] = prefix[0]).

The four u32 of `meta`: (hash, size_a, size_b, 0) -- see probe_trailer output.
"""
import glob, json, os, struct, sys
from collections import Counter

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
EXTS = (b".bmp", b".dds", b".ogg", b".ani", b".scr", b".tga", b".jpg", b".jpeg",
        b".png", b".luc", b".txt", b".ini", b".xml", b".wav", b".bik", b".cur",
        b".slk", b".fft", b".dat", b".mp3")


def decrypt(stem, seed):
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def scan_len(idx, p, seed, cap=1024):
    """Decrypt forward from p and return the printable path-char run length."""
    n = min(len(idx) - p, cap)
    if n < 4:
        return 0
    o = decrypt(idx[p:p + n], seed)
    L = 0
    while L < len(o) and o[L] in PATHCH:
        L += 1
    return L


def walk(idx, seed, limit=200000):
    """Chain the records. Returns list of (offset, name_len, name, meta)."""
    n = len(idx)
    p = 16
    L = scan_len(idx, p, seed)
    recs = []
    while 4 <= L <= 1024 and p + L + 20 <= n and len(recs) < limit:
        name = decrypt(idx[p:p + L], seed)
        meta = tuple(u32(idx, p + L + 4 * k) for k in range(5))
        recs.append((p, L, name, meta))
        L = meta[4]
        p = p + meta[4 - 4] * 0 + (recs[-1][1] + 20)
    return recs


def validity(recs, need_ext=False):
    """Fraction of names that are printable; count that end in a known ext."""
    if not recs:
        return 0.0, 0, 0
    ok = 0
    ext = 0
    for p, L, nm, meta in recs:
        if all(c in PATHCH for c in nm):
            ok += 1
        if nm.lower().endswith(EXTS):
            ext += 1
    return ok / len(recs), ok, ext


def best_seed(idx):
    """Brute-force k with seed=(k,0,0,0); pick the walk that stays printable."""
    best = None
    for k in range(256):
        seed = bytes([k, 0, 0, 0])
        # skip quickly: first name must be printable for at least 12 chars
        if scan_len(idx, 16, seed) < 12:
            continue
        recs = walk(idx, seed)
        frac, ok, ext = validity(recs)
        # require a long chain and high printable fraction
        if len(recs) < 5:
            continue
        score = (round(frac, 3), ok, len(recs))
        if best is None or score > best[0]:
            best = (score, seed, recs)
    return best


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    boom = os.path.join(root, "extracted/Boom")
    show = 0
    out = {}
    for path in sorted(glob.glob(os.path.join(boom, "*.idx"))):
        idx = open(path, "rb").read()
        if idx[:3] != b"\xca\xda\xef":
            continue
        nm = os.path.basename(path)[:-4]
        best = best_seed(idx)
        if best is None:
            print(f"{nm:16s} NO VALID SEED")
            continue
        (frac, ok, ext), seed, recs = best
        c = Counter()
        for _, _, n2, _ in recs:
            s = n2.decode("latin1")
            i = s.rfind(".")
            c[s[i:].lower() if i > 0 and "/" not in s[i:] else "(noext)"] += 1
        first = recs[0][2].decode("latin1")
        print(f"{nm:16s} seed={seed.hex(' ')} recs={len(recs):5d} printable={frac:.2f} "
              f"ext={ext}  first={first!r}")
        print(f"                 exts: {c.most_common(8)}")
        out[nm] = {
            "seed": list(seed),
            "count": len(recs),
            "printable_frac": frac,
            "with_ext": ext,
            "first": first,
            "names": [n2.decode("latin1") for _, _, n2, _ in recs],
        }
        if show:
            for _, _, n2, _ in recs[:show]:
                print("   ", n2.decode("latin1"))
    with open(os.path.join(root, "work/bigidx/names_big.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote work/bigidx/names_big.json")


if __name__ == "__main__":
    main()
