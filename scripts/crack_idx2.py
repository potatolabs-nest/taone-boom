#!/usr/bin/env python3
"""Crack the .idx name-stem transform, using the corrected record layout.

Record layout in an .idx (verified against ndadata bundles):

    u32 magic (ca da ef XX)
    u32 version (15)
    u32 count
    repeated count times:
        u32 stem_len
        stem_len bytes  <- obfuscated
        extension       <- PLAINTEXT, terminated by the first non-printable byte
        u32 size
        u32 size        (duplicate)
        u32 zero

The extension being plaintext is what makes this tractable: `.luc`, `.bmp`,
`.jpg` all appear in the clear, so a record's real stem length is known and the
candidate names from the Lua bundles can be aligned against it exactly.

Usage: python3 -I crack_idx2.py
"""
import glob, os, re, struct, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ND = os.path.join(ROOT, "extracted/Boom/ndadata")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from names_lua import lua_strings

ASSET_RE = re.compile(r"\.(bmp|jpg|jpeg|png|dds|ogg|ani|scr|tga|luc)$", re.I)


def parse_records(idx, limit=64):
    """Yield (stem, ext, size, size2, zero) using the layout above."""
    if len(idx) < 16:
        return
    count = struct.unpack_from("<I", idx, 8)[0]
    p = 16
    for _ in range(min(count, limit)):
        if p + 4 > len(idx):
            return
        ln = struct.unpack_from("<I", idx, p)[0]
        p += 4
        if ln == 0 or ln > 512 or p + ln > len(idx):
            return
        stem = idx[p:p + ln]
        p += ln
        # extension: printable ASCII up to 8 bytes
        e = p
        while e < len(idx) and 32 <= idx[e] < 127 and e - p < 8:
            e += 1
        ext = idx[p:e]
        p = e
        if p + 12 > len(idx):
            return
        a, b, c = struct.unpack_from("<3I", idx, p)
        p += 12
        yield stem, ext, a, b, c


def lua_names(base):
    p = os.path.join(ND, base + ".idd")
    if not os.path.exists(p):
        return []
    d = open(p, "rb").read()
    if d[:4] != b"\x1bLua":
        return []
    seen, out = set(), []
    for s in lua_strings(d):
        if ASSET_RE.search(s) and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def main():
    cribs = []          # (base, stem_ct, ext, [candidate full names])
    for f in sorted(glob.glob(os.path.join(ND, "*.idx"))):
        base = os.path.basename(f)[:-4]
        names = lua_names(base)
        if not names:
            continue
        idx = open(f, "rb").read()
        recs = list(parse_records(idx))
        if not recs:
            continue
        stem, ext, a, b, c = recs[0]
        cribs.append((base, stem, ext.decode("latin1"), names))

    print(f"cribs (bundle, record-0 stem, plaintext ext, known names): {len(cribs)}\n")
    print(f"{'bundle':22s} {'len':>4s} {'ext':>5s} {'size':>9s}  stem")
    for base, stem, ext, names in cribs:
        print(f"{base:22s} {len(stem):>4d} {ext:>5s} {'':>9s}  {stem[:26].hex(' ')}")
    print()

    # Do any known names share the stem's length? That is the alignment we need.
    print("=== can a known name supply the stem? ===")
    hits = 0
    for base, stem, ext, names in cribs:
        for n in names:
            nstem = n[:n.rfind(".")]
            if len(nstem) == len(stem):
                ks = bytes(x ^ y for x, y in zip(stem, nstem.encode("latin1")))
                print(f"  {base:22s} len={len(stem):>3d} vs {n[:34]:36s} ks={ks[:20].hex(' ')}")
                hits += 1
                break
    if not hits:
        print("  none — no known name matches a stem length exactly")
    print()

    # The extension is plaintext, so test whether the stem is a plain
    # difference of the plaintext: ct[i] = pt[i] ^ pt[i-k]
    print("=== testing ct[i] = pt[i] ^ pt[i-k] on the stem ===")
    for k in (1, 2, 3, 4, 5, 8):
        ok, tot = 0, 0
        for base, stem, ext, names in cribs:
            tot += 1
            for n in names:
                ns = n[:n.rfind(".")].encode("latin1")
                if len(ns) != len(stem):
                    continue
                good = sum(1 for i in range(k, len(stem)) if (ns[i] ^ ns[i - k]) == stem[i])
                if good / max(1, len(stem) - k) > 0.98:
                    ok += 1
                    break
        print(f"  k={k}: {ok}/{tot} bundles fit")

    print()
    print("=== keystream ct XOR name, for same-length names ===")
    for base, stem, ext, names in cribs:
        for n in names:
            ns = n[:n.rfind(".")].encode("latin1")
            if len(ns) != len(stem):
                continue
            ks = bytes(x ^ y for x, y in zip(stem, ns))
            print(f"  {base:22s} {n[:34]:36s} ks={ks.hex(' ')}")
            break


if __name__ == "__main__":
    main()
