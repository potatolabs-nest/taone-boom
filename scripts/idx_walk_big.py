#!/usr/bin/env python3
"""Walk the big `ca da ef` .idx family.  SOLVED by measurement.

FINDING 1 -- the body is ONE global self-differential XOR chain:
    plain[i] = raw[i] ^ plain[i-4]          (i >= 4 within the body)
    plain[0:4] = raw[0:4] ^ seed
The body starts at 0x10.  Measured: plain[1:4] == raw[1:4] on every archive
(seed = (k,0,0,0)), so only plain[0] is masked by one unknown byte k, recovered
by demanding that the record chain walks.

FINDING 2 -- records are  [name: L bytes][trailer: 20 bytes]:
    trailer = u32 hash | u32 size_a | u32 size_b | u32 zero | u32 L_next
and the next record is at p + L + 20.  The FIRST record's length is the leading
printable run (no length is stored for it).

FINDING 3 -- names are ASSET GROUP NAMES, often with NO file extension
('Bonus/Airplane1', 'Game/BigBattle_Timer', 'Game/AIBattle_SuperStar'), which is
why every earlier extension-filtered scan rejected them.

Usage:
  python3 -I idx_walk_big.py                # all big idx
  python3 -I idx_walk_big.py FxStage --show 10
"""
import argparse, glob, json, os, struct, sys

ROOT = "/Users/hieu/Workspaces/taone"
BOOM = os.path.join(ROOT, "extracted/Boom")
OUT = os.path.join(ROOT, "work/idx_layout")
OFF = 0x10
TRAILER = 20
RUNCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def decode(raw, k, off=OFF):
    n = len(raw)
    m = n - off
    out = bytearray(m)
    out[0] = raw[off] ^ k
    for i in range(1, min(4, m)):
        out[i] = raw[off + i]           # seed[1:4] == 0 (measured)
    for i in range(4, m):
        out[i] = raw[off + i] ^ out[i - 4]
    return bytes(out)


def walk(pt, limit=400000):
    """Chain records. Returns (recs, consumed, ok_end)."""
    n = len(pt)
    i = 0
    while i < n and pt[i] in RUNCH:
        i += 1
    L = i
    recs = []
    p = 0
    while 2 <= L <= 4096 and p + L + TRAILER <= n and len(recs) < limit:
        nm = pt[p:p + L]
        tr = [u32(pt, p + L + 4 * j) for j in range(5)]
        recs.append((p, L, nm, tr))
        Lnext = tr[4]
        p = p + L + TRAILER
        L = Lnext
    return recs, p


def solve_k(raw, off=OFF):
    """Pick k whose chain walks farthest and stays printable.

    Scoring uses only a short prefix of the body (256 * 8 KB = 2 MB), so this
    stays fast even on the 900 KB indexes; the winner is then re-walked whole.
    """
    best = None
    for k in range(256):
        pt = decode(raw[:off + 8192], k, off)
        recs, end = walk(pt)
        sc = (end, len(recs))
        if best is None or sc > best[0]:
            best = (sc, k)
    k = best[1]
    pt = decode(raw, k, off)
    recs, end = walk(pt)
    return (end, len(recs)), k, pt, recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archives", nargs="*")
    ap.add_argument("--show", type=int, default=8)
    args = ap.parse_args()

    out = {}
    total_names = 0
    for path in sorted(glob.glob(os.path.join(BOOM, "*.idx"))):
        base = os.path.basename(path)[:-4]
        if args.archives and base not in args.archives:
            continue
        raw = open(path, "rb").read()
        if len(raw) < 0x20:
            continue
        (end, nrec), k, pt, recs = solve_k(raw)
        idd = os.path.join(BOOM, base + ".idd")
        iddsz = os.path.getsize(idd) if os.path.exists(idd) else 0
        hdr = [u32(raw, 4 * j) for j in range(4)]
        exts = {}
        for _, _, nm, _ in recs:
            s = nm.decode("latin1", "replace")
            j = s.rfind(".")
            e = s[j:].lower() if j > 0 and "/" not in s[j:] else "(none)"
            exts[e] = exts.get(e, 0) + 1
        frac = end / len(pt) if pt else 0
        out[base] = {
            "k": k, "hdr": hdr, "idx_size": len(raw), "idd_size": iddsz,
            "header_count_a": hdr[2], "header_count_b": hdr[3],
            "records": len(recs), "body": len(pt), "chain_end": end,
            "body_frac": round(frac, 5),
            "names": [{"off": p, "len": L, "name": nm.decode("latin1", "replace"),
                       "hash": tr[0], "size_a": tr[1], "size_b": tr[2],
                       "zero": tr[3]} for p, L, nm, tr in recs],
            "exts": exts,
        }
        total_names += len(recs)
        print(f"{base:16s} k={k:#04x} hdr_counts=({hdr[2]},{hdr[3]}) recs={len(recs):>5,} "
              f"body={len(pt):>10,} walked={end:>10,} ({frac*100:5.1f}%) idd={iddsz:>11,}")
        print(f"                 exts={sorted(exts.items(), key=lambda t:-t[1])[:6]}")
        for p, L, nm, tr in recs[:args.show]:
            print(f"    @{p:07x} L={L:3d} {nm.decode('latin1','replace')!r} "
                  f"hash={tr[0]:#x} a={tr[1]:,} b={tr[2]:,} z={tr[3]}")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "walk_big.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nTOTAL big-idx names: {total_names:,} -> {os.path.join(OUT,'walk_big.json')}")


if __name__ == "__main__":
    main()
