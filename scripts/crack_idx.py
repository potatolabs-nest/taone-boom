#!/usr/bin/env python3
"""Work out the .idx name-field transform using known plaintext.

We finally have real cribs: the ndadata bundles that are compiled Lua contain
plaintext asset paths, and 15 of them have a sibling .idx. That pairing gives
(plaintext name, ciphertext name field) for the same record.

Earlier hand analysis suggested the keystream equals an earlier slice of the
plaintext, i.e. a self-differential transform. This script tests that and a
family of related hypotheses against EVERY known pair and reports the first
that fits all of them exactly.

Usage: python3 -I crack_idx.py
"""
import glob, json, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ND = os.path.join(ROOT, "extracted/Boom/ndadata")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from names_lua import lua_strings

ASSET_RE = re.compile(r"\.(bmp|jpg|jpeg|png|dds|ogg|ani|scr|tga)$", re.I)


def triples(idx):
    """Positions of the (size, size, 0) u32 triple that ends each record."""
    out = []
    for q in range(16, len(idx) - 12):
        a, b, c = struct.unpack_from("<3I", idx, q)
        if a == b and 0 < a < 1 << 31 and c == 0:
            out.append(q)
    return out


def names_for(base):
    p = os.path.join(ND, base + ".idd")
    if not os.path.exists(p):
        return []
    data = open(p, "rb").read()
    if data[:4] != b"\x1bLua":
        return []
    seen, out = set(), []
    for s in lua_strings(data):
        if ASSET_RE.search(s) and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def main():
    pairs = []          # (base, ciphertext_name_field, [candidate plaintexts])
    for f in sorted(glob.glob(os.path.join(ND, "*.idx"))):
        base = os.path.basename(f)[:-4]
        idx = open(f, "rb").read()
        ns = names_for(base)
        if not ns:
            continue
        t = triples(idx)
        if not t:
            continue
        # record 0's name field runs from 16 up to the first triple
        ct = idx[16:t[0]]
        pairs.append((base, ct, ns))

    print(f"bundles with both a crib and a parseable record: {len(pairs)}\n")
    for base, ct, ns in pairs:
        print(f"--- {base}: field={len(ct)}B, {len(ns)} known names")
        for n in ns[:3]:
            print(f"      {n}")
        print(f"      ct: {ct[:32].hex(' ')}")

    # ---- hypothesis: ct[i] = pt[i] ^ pt[i-k] for i>=k, with ct[:k] = pt[:k] ^ iv
    print("\n=== testing ct[i] = pt[i] ^ pt[i-k] ===")
    for k in (1, 2, 3, 4, 6, 8):
        ok_all, tried = True, 0
        for base, ct, ns in pairs:
            fit = False
            for pt in ns:
                b = pt.encode("latin1", "ignore")
                if len(b) < k + 8:
                    continue
                # allow the field to be a suffix/prefix window of the name
                for off in range(0, max(1, len(b) - len(ct) + 1)):
                    seg = b[off:off + len(ct)]
                    if len(seg) < len(ct):
                        continue
                    good = sum(1 for i in range(k, len(ct)) if (seg[i] ^ seg[i - k]) == ct[i])
                    total = len(ct) - k
                    if total and good / total > 0.98:
                        fit = True
                        break
                if fit:
                    break
            tried += 1
            if not fit:
                ok_all = False
                break
        print(f"  k={k}: {'FITS ALL' if ok_all else 'no'}")

    # ---- hypothesis: a plain repeating XOR key of some length
    print("\n=== testing repeating XOR key ===")
    for klen in range(2, 33):
        okall = True
        for base, ct, ns in pairs:
            found = False
            for pt in ns:
                b = pt.encode("latin1", "ignore")
                if len(b) < len(ct):
                    continue
                if bytes(x ^ y for x, y in zip(ct, b[:len(ct)]))[:klen] * 99:
                    ks = bytes(x ^ y for x, y in zip(ct, b[:len(ct)]))
                    rep = (ks[:klen] * (len(ks) // klen + 1))[:len(ks)]
                    if ks == rep:
                        found = True
                        break
            if not found:
                okall = False
                break
        if okall:
            print(f"  keylen={klen}: FITS ALL")
    print("  (nothing printed above = no repeating XOR key fits)")

    # ---- dump the keystream for record 0 of each bundle, to eyeball structure
    print("\n=== keystream (ct XOR best-matching name) ===")
    for base, ct, ns in pairs[:6]:
        for pt in ns:
            b = pt.encode("latin1", "ignore")
            if len(b) < len(ct):
                continue
            ks = bytes(x ^ y for x, y in zip(ct, b[:len(ct)]))
            print(f"  {base:22s} vs {pt[:28]:30s} ks={ks[:24].hex(' ')}")
            break


if __name__ == "__main__":
    main()
