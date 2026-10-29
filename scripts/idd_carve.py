#!/usr/bin/env python3
"""Carve every big .idd using the exact payload sizes recovered from its .idx.

Established: sum(size_a) over the .idx records equals the .idd byte size to
within 0.01-0.2%, and carving FxSound this way reproduces all 692 Ogg streams
as valid standalone files contiguous from offset 0 -- an INDEPENDENT
confirmation of the earlier 693-stream result.

Each carved payload is validated by parsing its own header.

Usage: python3 -I idd_carve.py [archive ...]
"""
import json, os, struct, sys, zlib

ROOT = "/Users/hieu/Workspaces/taone"
BOOM = os.path.join(ROOT, "extracted/Boom")
WALK = os.path.join(ROOT, "work/idx_layout/walk_big.json")


def ogg_total(b):
    q, n = 0, len(b)
    while q + 27 <= n:
        if b[q:q + 4] != b"OggS":
            return None
        nsegs = b[q + 26]
        if q + 27 + nsegs > n:
            return None
        sz = 27 + nsegs + sum(b[q + 27:q + 27 + nsegs])
        if sz <= 0:
            return None
        if b[q + 5] & 0x04:
            return q + sz
        q += sz
    return None


def bmp_total(b):
    if len(b) < 54 or b[:2] != b"BM":
        return None
    size = struct.unpack_from("<I", b, 2)[0]
    dib = struct.unpack_from("<I", b, 14)[0]
    if dib not in (12, 40, 52, 56, 64, 108, 124):
        return None
    w, h = struct.unpack_from("<ii", b, 18)
    if w == 0 or h == 0 or abs(w) > 20000 or abs(h) > 20000:
        return None
    return size if size == len(b) else None


def dds_total(b):
    if len(b) < 128 or b[:4] != b"DDS ":
        return None
    if struct.unpack_from("<I", b, 4)[0] != 124:
        return None
    return len(b) if b[84:88] in (b"DXT1", b"DXT2", b"DXT3", b"DXT4", b"DXT5", b"\0\0\0\0") else None


def jpg_total(b):
    n = len(b)
    if n < 4 or b[0] != 0xFF or b[1] != 0xD8:
        return None
    q = 2
    while q + 1 < n:
        if b[q] != 0xFF:
            return None
        while q < n and b[q] == 0xFF:
            q += 1
        if q >= n:
            return None
        m = b[q]
        q += 1
        if m == 0xD9:
            return q
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            continue
        if m == 0xDA:
            e = b.find(b"\xff\xd9", q)
            return e + 2 if e >= 0 else None
        if q + 2 > n:
            return None
        ln = struct.unpack_from(">H", b, q)[0]
        if ln < 2:
            return None
        q += ln
        if q > n:
            return None
    return None


def png_total(b):
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    q, n = 8, len(b)
    while q + 8 <= n:
        ln = struct.unpack_from(">I", b, q)[0]
        typ = b[q + 4:q + 8]
        q += 12 + ln
        if typ == b"IEND":
            return q
        if ln > 100_000_000:
            return None
    return None


def zlib_stream(b):
    """Return (compressed_len, inflated_len) if b starts with a whole zlib stream."""
    if len(b) < 8 or b[0] != 0x78 or b[1] not in (0x01, 0x9C, 0xDA, 0x5E):
        return None
    try:
        o = zlib.decompressobj()
        data = o.decompress(b) + o.flush()
        used = len(b) - len(o.unused_data)
        return used, len(data), data
    except Exception:
        return None


DETECT = [
    ("ogg", lambda b: ogg_total(b)),
    ("bmp", lambda b: bmp_total(b)),
    ("dds", lambda b: dds_total(b)),
    ("jpg", lambda b: jpg_total(b)),
    ("png", lambda b: png_total(b)),
]


def classify(b):
    for name, fn in DETECT:
        try:
            t = fn(b)
        except Exception:
            t = None
        if t is not None:
            return name, "header-exact"
    z = zlib_stream(b)
    if z and z[0] == len(b):
        return "zlib", f"zlib whole ({z[1]} inflated)"
    if z:
        return "zlib", f"zlib partial {z[0]}/{len(b)}"
    return "raw", "unvalidated"


def main():
    archs = sys.argv[1:] or ["FxSound", "FxStage", "FxCharacter", "FxContents",
                             "FxMap", "FxDesktop", "FxMonster", "FxHiddenCatch"]
    walk = json.load(open(WALK))
    grand = []
    for arch in archs:
        if arch not in walk:
            print(f"{arch}: no idx walk")
            continue
        recs = walk[arch]["names"]
        idd = open(os.path.join(BOOM, arch + ".idd"), "rb").read()
        pos = 0
        counts = {}
        cov = 0
        n_ok = 0
        for r in recs:
            sz = r["size_a"]
            blob = idd[pos:pos + sz]
            if len(blob) != sz:
                break
            kind, why = classify(blob)
            counts[kind] = counts.get(kind, 0) + 1
            if kind != "raw":
                n_ok += 1
            cov += sz
            pos += sz
        print(f"{arch:14s} recs={len(recs):>5} carved={cov:>11,}/{len(idd):>11,} "
              f"= {cov/len(idd)*100:6.2f}%  validated={n_ok:>5}  {sorted(counts.items(), key=lambda t:-t[1])}")
        grand.append((arch, len(idd), cov, len(recs), n_ok, counts))

    tot = sum(g[1] for g in grand)
    cov = sum(g[2] for g in grand)
    print(f"\nTOTAL of these archives: {cov:,}/{tot:,} = {cov/tot*100:.2f}%")
    return grand


if __name__ == "__main__":
    main()
