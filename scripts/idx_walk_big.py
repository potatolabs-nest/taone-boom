#!/usr/bin/env python3
"""Walk the big Fx*.idx record chain.

Layout (confirmed by hand on FxStage record 0..3):

  offset 0x00: magic 'ca da ef XX'      (u32)
  offset 0x04: u32 version = 15
  offset 0x08: u32 count_a
  offset 0x0c: u32 count_b
  offset 0x10: first record

  record = [ head (obfuscated name, L bytes) ]
           [ 16 bytes meta ]
           [ u32 L_next ]            <- length of the NEXT record's head
  => next record starts at p + L + 20

  L for record 0 is not stored before it; recover it by scanning the
  decrypted run (the byte after the name is never a path character).
"""
import struct, sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")


def decrypt(stem, prefix):
    seed = bytes(stem[i] ^ prefix[i] for i in range(4))
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def scan_len(idx, p, prefix, cap=512):
    w = idx[p:p + cap]
    if len(w) < 4:
        return 0
    o = decrypt(w, prefix)
    L = 0
    while L < len(o) and o[L] in PATHCH:
        L += 1
    return L


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def walk(idx, prefix=b"Game/", verbose=0):
    n = len(idx)
    p = 16
    L = scan_len(idx, p, prefix)
    recs = []
    while L >= 4 and p + L + 20 <= n:
        head = idx[p:p + L]
        name = decrypt(head, prefix)
        meta = [u32(idx, p + L + 4 * k) for k in range(5)]
        recs.append((p, L, name, meta))
        if verbose:
            print(f"p={p:#08x} L={L:3d} meta={[hex(m) for m in meta[:4]]} next={meta[4]:3d} {name.decode('latin1')}")
        nxt = meta[4]
        p = p + L + 20
        L = nxt
    return recs


def main():
    idx = open(sys.argv[1], "rb").read()
    prefix = sys.argv[2].encode() if len(sys.argv) > 2 else b"Game/"
    v = 1 if "-v" in sys.argv else 0
    recs = walk(idx, prefix, v)
    print(f"{len(recs)} records walked of file {len(idx)} bytes; end p={recs[-1][0]+recs[-1][1]+20 if recs else 16:#x}")
    # extension histogram
    from collections import Counter
    c = Counter()
    bad = 0
    for p, L, name, meta in recs:
        s = name.decode("latin1")
        if any(ord(ch) < 32 or ord(ch) > 126 for ch in s):
            bad += 1
        i = s.rfind(".")
        c[s[i:].lower() if i > 0 else "(noext)"] += 1
    print("extensions:", c.most_common(20))
    print("non-printable names:", bad)


if __name__ == "__main__":
    main()
