#!/usr/bin/env python3
"""Recover .idx names with the self-differential transform.

Layout (verified against the ndadata bundles):

    u32 magic (ca da ef XX) | u32 version (15) | u32 count
    per record:
        stem        <- obfuscated name stem, length implied by the record
        extension   <- PLAINTEXT, e.g. ".luc" / ".bmp" / ".jpg"
        u32 size | u32 size | u32 zero

Transform, established from a known plaintext pair on MonWarsRank2nd:

    stem[i] = name[i] ^ name[i-4]        for i >= 4
    stem[0..3] = name[0..3] ^ IV

so name[i] = stem[i] ^ name[i-4], which needs only the first four plaintext
bytes. Those are recoverable because every path in this client starts with a
directory such as "Quest/" or "PopupEvent/".

Usage: python3 -I crack_idx3.py [--verify]
"""
import glob, os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ND = os.path.join(ROOT, "extracted/Boom/ndadata")

# directories this client uses, most frequent first
PREFIXES = ["Quest/", "PopupEvent/", "Item/", "Icon/", "UI/", "Sound/",
            "Effect/", "Character/", "Avatar/", "Stage/", "Data/", "Lua/"]


def parse_stems(idx):
    """Yield (stem_bytes, ext_bytes, off) walking the record chain.

    The extension is plaintext and always follows the stem, which anchors the
    walk; the (size, size, 0) triple that follows confirms the boundary.
    """
    if len(idx) < 16:
        return
    p = 16
    n = len(idx)
    while p < n:
        # find the next plaintext extension
        e = p
        while e < n and not (idx[e] == 0x2E and 32 <= idx[e+1] < 127):
            e += 1
        if e >= n - 4:
            return
        x = e
        while x < n and 32 <= idx[x] < 127 and x - e < 8:
            x += 1
        ext = idx[e:x]
        stem = idx[p:e]
        if not stem:
            p = x
            continue
        yield stem, ext, p
        # advance past the triple if present
        q = x
        if q + 12 <= n:
            a, b, c = struct.unpack_from("<3I", idx, q)
            if a == b and c == 0:
                q += 12
            else:
                q += 4
        p = q


def decrypt(stem, prefix):
    """name[i] = stem[i] ^ name[i-4]; seed the first 4 from a known prefix."""
    if len(prefix) < 4:
        return None
    name = bytearray(len(stem))
    for i in range(4):
        name[i] = stem[i] ^ ord(prefix[i])
    for i in range(4, len(stem)):
        name[i] = stem[i] ^ name[i - 4]
    return bytes(name)


def score(name):
    """How much this looks like a real asset path."""
    if not name:
        return -999
    printable = sum(1 for b in name if 32 <= b < 127)
    if printable != len(name):
        return -999
    s = name.decode("latin1")
    pts = 0
    if "/" in s or "\\" in s:
        pts += 2
    for p in PREFIXES:
        if s.startswith(p):
            pts += 6
    if s.endswith((".bmp", ".jpg", ".png", ".luc", ".dds", ".ani", ".scr", ".ogg")):
        pts += 3
    # real names are mostly [A-Za-z0-9_/.-]
    good = sum(1 for c in s if c.isalnum() or c in "_/.-")
    pts += 4 * good / len(s)
    return pts


def main():
    verify = "--verify" in sys.argv
    total_ok = total = 0
    samples = []

    for f in sorted(glob.glob(os.path.join(ND, "*.idx"))):
        idx = open(f, "rb").read()
        base = os.path.basename(f)[:-4]
        recs = list(parse_stems(idx))
        if not recs:
            continue
        ok = 0
        for stem, ext, off in recs:
            best, bestname = -1e9, None
            for pfx in PREFIXES:
                nm = decrypt(stem, pfx)
                if nm is None:
                    continue
                sc = score(nm)
                if sc > best:
                    best, bestname = sc, nm
            total += 1
            if best > 8:
                ok += 1
                if len(samples) < 24:
                    samples.append((base, bestname.decode("latin1") + ext.decode("latin1")))
        total_ok += ok
        if recs:
            print(f"{base:24s} {ok:>4d}/{len(recs):<4d} names recovered")

    print()
    print(f"TOTAL: {total_ok}/{total} records decoded to a plausible path")
    if samples:
        print("\nsamples:")
        seen = set()
        for b, nm in samples:
            if nm in seen:
                continue
            seen.add(nm)
            print(f"  {b:22s} {nm}")


if __name__ == "__main__":
    main()
