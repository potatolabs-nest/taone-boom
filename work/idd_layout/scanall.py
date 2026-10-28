"""Scan an .idx for all offsets that decode (differential cipher, prefix Game)
to a clean printable NUL-terminated name.  Report the record deltas."""
import os, sys
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
OK = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-. /~+()[]@")
PREFIX = b'Game'


def dec(d, p, maxlen=200):
    """seed[i] = stem[i] ^ PREFIX[i]; name[i] = stem[i] ^ (seed[i] if i<4 else name[i-4])"""
    out = bytearray()
    for i in range(maxlen):
        if p + i >= len(d):
            return None
        c = d[p + i] ^ (PREFIX[i] if i < 4 else out[i - 4])
        if c == 0:
            return bytes(out)
        if c not in OK:
            return None
        out.append(c)
    return None


name = sys.argv[1]
minlen = int(sys.argv[2]) if len(sys.argv) > 2 else 8
d = open(os.path.join(B, name + '.idx'), 'rb').read()
n = len(d)
hits = []
for p in range(0x10, n - 6):
    nm = dec(d, p)
    if nm is not None and len(nm) >= minlen:
        hits.append((p, len(nm), nm))
print(f"{name}.idx {n:,}  clean names(len>={minlen}): {len(hits)}")
for p, ln, nm in hits[:25]:
    print(f"  {p:#08x} len={ln:3d} {nm.decode('latin1')!r}")
print("  ...")
for p, ln, nm in hits[-12:]:
    print(f"  {p:#08x} len={ln:3d} {nm.decode('latin1')!r}")
deltas = Counter(hits[i + 1][0] - hits[i][0] for i in range(len(hits) - 1))
print("  delta:", deltas.most_common(10))
print("  delta-namelen:", Counter(hits[i + 1][0] - hits[i][0] - hits[i][1]
                                 for i in range(len(hits) - 1)).most_common(10))
