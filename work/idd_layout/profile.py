"""Profile one .idd: entropy per 64 KB block, zlib header density, and
candidate boundaries."""
import sys, os, math, struct, zlib
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def ent(b):
    if not b: return 0
    c = Counter(b); n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


name = sys.argv[1]
d = open(os.path.join(B, name + '.idd'), 'rb').read()
n = len(d)
W = 65536
print(f"{name}.idd {n:,}  blocks={n//W}")

# zlib header variants
for magic in (b'\x78\xda', b'\x78\x9c', b'\x78\x01', b'\x78\x5e'):
    cnt = sum(1 for i in range(0, n - 1) if d[i:i+2] == magic)
    print(f"  count of {magic.hex()}: {cnt}")

# entropy profile coarse
print("\n  block  offset       entropy  zlib78da  DDS/BM/JPEG")
for bi in range(0, n // W):
    o = bi * W
    blk = d[o:o + W]
    e = ent(blk)
    print(f"  {bi:5d}  {o:>11,}  {e:.3f}", end='')
    if bi % 8 == 7 or bi < 4:
        print()
    else:
        print('', end='\r')
print()
# where does entropy change sharply?
prev = None
print("\nSharp entropy changes (>0.8):")
for bi in range(0, n // W):
    o = bi * W
    e = ent(d[o:o + W])
    if prev is not None and abs(e - prev) > 0.8:
        print(f"   {o:>11,}  {prev:.2f} -> {e:.2f}")
    prev = e
