"""Test candidate byte transforms on structured regions of the .idd.

The .idx name cipher is self-differential (name[i] = stem[i] ^ name[i-4]).
Test whether the .idd body uses the same trick, or a fixed period-XOR, or a
single-byte XOR.  A correct transform should collapse entropy or reveal magic.
"""
import sys, os, math, struct
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def ent(b):
    if not b: return 0
    c = Counter(b); n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


name = sys.argv[1]
off = int(sys.argv[2], 0)
ln = int(sys.argv[3]) if len(sys.argv) > 3 else 65536
d = open(os.path.join(B, name + '.idd'), 'rb').read()
blk = d[off:off + ln]
print(f"{name} @ {off:#x} len={ln}  raw entropy={ent(blk):.3f}")

MAGICS = [b'OggS', b'BM', b'DDS ', b'\x89PNG', b'\xff\xd8\xff', b'RIFF', b'PK\x03\x04']


def score(b):
    return ent(b), sum(b.count(0) for _ in [0])


# differential decode i>=k:  out[i] = b[i] ^ out[i-k]
for k in (1, 2, 4, 8, 16):
    out = bytearray(blk)
    for i in range(k, len(blk)):
        out[i] = blk[i] ^ out[i - k]
    e = ent(out)
    mg = [m for m in MAGICS if bytes(m) in bytes(out[:4096])]
    print(f"  diff-decode k={k:2d}: entropy={e:.3f} magic_in_first4k={mg} zero={bytes(out).count(0)}")

# differential ENCODE order: out[i] = b[i] ^ b[i-k]
for k in (1, 2, 4, 8, 16):
    out = bytearray(len(blk))
    for i in range(len(blk)):
        out[i] = blk[i] ^ (blk[i - k] if i >= k else 0)
    e = ent(out)
    mg = [m for m in MAGICS if bytes(m) in bytes(out[:4096])]
    print(f"  diff-xor   k={k:2d}: entropy={e:.3f} magic_in_first4k={mg} zero={bytes(out).count(0)}")

# plain XOR byte
best = []
for k in range(256):
    out = bytes(x ^ k for x in blk)
    e = ent(out)
    mg = [m for m in MAGICS if m in out[:4096]]
    if mg:
        best.append((k, e, mg))
print("  single-byte XOR hits:", best[:5])
