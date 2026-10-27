#!/usr/bin/env python3
"""Decrypt .idx names.

Layout (confirmed against ndadata bundles):

    u32 magic (ca da ef XX) | u32 version (15) | u32 count
    per record:
        u32 stem_len
        stem[stem_len]        <- obfuscated
        u32 size | u32 size | u32 zero

Transform, derived from a known plaintext pair on MonWarsRank2nd record 1
(ct XOR pt revealed the plaintext shifted by 4):

    stem[i] = name[i] ^ name[i-4]     for i >= 4
    stem[i] = name[i] ^ iv            for i <  4, where iv occupies byte 0

so name[i] = stem[i] ^ name[i-4]. Only the four seed bytes are unknown, and the
IV is a single byte, so it is brute-forced and the winner chosen by whether the
result reads as a real asset path.

Usage: python3 -I crack_idx4.py [--dump DIR]
"""
import glob, json, os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOM = os.path.join(ROOT, "extracted/Boom")
ND = os.path.join(BOOM, "ndadata")

EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".dds", ".ogg", ".ani", ".scr",
        ".tga", ".luc", ".slk", ".txt", ".xml", ".cur", ".ico", ".wav",
        ".mp3", ".dat", ".ini", ".fft", ".bik")


def parse_records(idx):
    """Yield (stem, size, offset).

    Records start at 16 and each stem runs up to the plaintext extension, so
    the extension is the anchor: find the next '.' followed by a printable run.
    Verified on MonWarsRank2nd record 0, whose stem decrypts to exactly
    "Quest/MonWarsRank2nd.luc".

    The magic differs between index families (big archives use ca da ef, the
    ndadata bundles use fc 01 b2 05), so it is not a usable gate.
    """
    if len(idx) < 20:
        return
    p, n = 16, len(idx)
    while p < n - 4:
        e = p
        while e < n - 1:
            if idx[e] == 0x2E and (chr(idx[e + 1]).isalnum()):
                break
            e += 1
        if e >= n - 1:
            return
        x = e + 1
        while x < n and 32 <= idx[x] < 127 and x - e < 9:
            x += 1
        stem = idx[p:e]
        if stem:
            size = struct.unpack_from("<I", idx, x)[0] if x + 4 <= n else 0
            yield stem, size, p
        # step over the (size, size, 0) triple when present
        q = x
        if q + 12 <= n:
            a, b, c = struct.unpack_from("<3I", idx, q)
            q += 12 if (a == b and c == 0) else 4
        else:
            q = x + 4
        p = q


def decrypt(stem, iv):
    """name[i] = stem[i] ^ name[i-4].

    All four seed bytes use the same iv; established from MonWarsRank2nd
    record 0, where every stem byte XORs against the plaintext four positions
    back, seed bytes included ("Ques" came out of iv = 0x22).
    """
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (iv if i < 4 else out[i - 4])
    return bytes(out)


def score(name):
    """How strongly this reads as a real asset path (higher is better)."""
    if not name:
        return -1e9
    if any(b < 32 or b > 126 for b in name):
        return -1e9
    s = name.decode("latin1")
    pts = 0.0
    if "/" in s:
        pts += 3
    if s.startswith(("Quest/", "PopupEvent/", "Item/", "Icon/", "UI/")):
        pts += 5
    if s.lower().endswith(EXTS):
        pts += 4
    ok = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
    pts += 6 * sum(1 for c in s if c in ok) / len(s)
    return pts


def recover(stem):
    """Brute-force the seed byte; return (name, score) for the best reading."""
    best, best_s = None, -1e9
    for iv in range(256):
        nm = decrypt(stem, iv)
        s = score(nm)
        if s > best_s:
            best, best_s = nm, s
    return best, best_s


def main():
    dump = None
    if "--dump" in sys.argv:
        dump = sys.argv[sys.argv.index("--dump") + 1]
        os.makedirs(dump, exist_ok=True)

    index = {}
    tot = ok = 0
    per_archive = {}

    for idx_path in sorted(glob.glob(os.path.join(BOOM, "*.idx")) +
                           glob.glob(os.path.join(ND, "*.idx"))):
        base = os.path.basename(idx_path)[:-4]
        rel = "ndadata/" + base if os.path.dirname(idx_path) == ND else base
        try:
            idx = open(idx_path, "rb").read()
        except OSError:
            continue
        recs = list(parse_records(idx))
        if not recs:
            continue
        names = []
        for stem, size, off in recs:
            nm, sc = recover(stem)
            tot += 1
            good = sc > 9
            ok += 1 if good else 0
            entry = {"offset": off, "size": size,
                     "name": nm.decode("latin1") if good else None,
                     "confidence": "high" if sc > 12 else ("medium" if good else "low")}
            names.append(entry)
        per_archive[rel] = names
        print(f"{rel:28s} {sum(1 for e in names if e['name']):>4d}/{len(recs):<4d} named")

    print()
    print(f"TOTAL records: {tot}   decoded to a path: {ok} ({100*ok/max(1,tot):.1f}%)")

    out = os.path.join(ROOT, "work/idx_names.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(per_archive, fh, indent=1)
    print(f"wrote {out}")

    print("\nsamples:")
    shown = 0
    for rel, names in per_archive.items():
        for e in names:
            if e["name"]:
                print(f"  {rel:26s} {e['name']}")
                shown += 1
                break
        if shown >= 25:
            break


if __name__ == "__main__":
    main()
