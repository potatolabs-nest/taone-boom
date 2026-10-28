"""Find record starts in a ca da ef .idx by validating the differential decode.

A record name is stored as stem bytes with name[i] = stem[i] ^ name[i-4] for
i>=4; only the 4-byte seed is unknown.  Rather than guess the seed, require the
decoded tail to be clean ASCII *and* its XOR-implied seed to be consistent with
a known directory prefix.  A garbage offset almost never decodes to a path.
"""
import sys, os, struct
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
OK = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-. /~+()[]@")


def try_decode(d, p, maxlen=260, require_prefix=False, prefix=b'Game/'):
    """Return (name, namelen_incl_nul) or (None, None)."""
    n = len(d)
    # seed from the (unknown) first 4 plaintext bytes; we require them printable
    # and (optionally) equal to the known directory prefix.
    if require_prefix:
        # for i<4 the plaintext is the prefix itself; seed[i] = stem[i] ^ prefix[i]
        if d[p:p + 4] != bytes(a ^ b for a, b in zip(d[p:p + 4], prefix[:4])):
            pass
        seed = bytes(a ^ b for a, b in zip(d[p:p + 4], prefix[:4]))
    else:
        seed = None
    out = bytearray()
    for i in range(0, maxlen):
        if i < 4:
            c = d[p + i] ^ (seed[i] if seed is not None else d[p + i])
        else:
            c = d[p + i] ^ out[i - 4]
        if c == 0:
            nm = bytes(out)
            if require_prefix and not nm.startswith(prefix):
                return None, None
            return nm, i + 1
        if c not in OK:
            return None, None
        out.append(c)
    return None, None


def scan(name, prefix=b'Game/'):
    d = open(os.path.join(B, name + '.idx'), 'rb').read()
    n = len(d)
    print(f"=== {name}.idx size={n:,} hdr={struct.unpack_from('<III',d,4)}")
    # require the known prefix so garbage offsets are rejected hard
    hits = []
    for p in range(0x10, n - 8):
        nm, ln = try_decode(d, p, require_prefix=True, prefix=prefix)
        if nm is not None:
            hits.append((p, ln, nm))
    print(f"  prefix-valid record starts: {len(hits)}")
    for p, ln, nm in hits[:8]:
        print(f"   {p:#08x} len={ln:3d} {nm.decode('cp949','replace')!r}")
    print("  ...")
    for p, ln, nm in hits[-8:]:
        print(f"   {p:#08x} len={ln:3d} {nm.decode('cp949','replace')!r}")
    # record-to-record deltas
    if len(hits) > 2:
        deltas = [hits[i + 1][0] - hits[i][0] for i in range(len(hits) - 1)]
        from collections import Counter
        print("  delta common:", Counter(deltas).most_common(6))
        print("  delta = prev_namelen + ? :",
              Counter(deltas[i] - hits[i][1] for i in range(len(deltas))).most_common(6))
    return hits


if __name__ == '__main__':
    nm = sys.argv[1] if len(sys.argv) > 1 else 'FxStage'
    scan(nm)
