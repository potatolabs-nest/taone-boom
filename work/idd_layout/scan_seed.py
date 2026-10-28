"""With the per-archive seed known (from record 0), scan the whole .idx for
offsets that decode to a clean NUL-terminated name, and inspect the deltas.
"""
import os, sys
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
OK = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-. /~+()[]@")


def dec(d, p, seed, maxlen=200):
    out = bytearray()
    for i in range(maxlen):
        if p + i >= len(d):
            return None
        c = d[p + i] ^ (seed[i] if i < 4 else out[i - 4])
        if c == 0:
            return bytes(out)
        if c not in OK:
            return None
        out.append(c)
    return None


name = sys.argv[1]
seed = bytes.fromhex(sys.argv[2])
d = open(os.path.join(B, name + '.idx'), 'rb').read()
n = len(d)
hits = []
for p in range(0, n - 6):
    nm = dec(d, p, seed)
    if nm is not None and len(nm) >= 4:
        hits.append((p, len(nm) + 1, nm))
print(f"{name}.idx {n:,} seed={seed.hex(' ')}  clean names: {len(hits)}")
for p, ln, nm in hits[:20]:
    print(f"  {p:#08x} len={ln:3d} {nm.decode('latin1')!r}")
print("  ...")
for p, ln, nm in hits[-10:]:
    print(f"  {p:#08x} len={ln:3d} {nm.decode('latin1')!r}")
if len(hits) > 1:
    deltas = Counter(hits[i + 1][0] - hits[i][0] for i in range(len(hits) - 1))
    print("  delta (next_start - this_start):", deltas.most_common(8))
    print("  delta - namelen:", Counter(hits[i + 1][0] - hits[i][0] - hits[i][1]
                                        for i in range(len(hits) - 1)).most_common(8))
