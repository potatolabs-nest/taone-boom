import sys, os, math, struct
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def ent(b):
    if not b: return 0
    c = Counter(b)
    n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


name = sys.argv[1]
d = open(os.path.join(B, name + '.idd'), 'rb').read()
n = len(d)
print(f"{name} size={n:,}")
# entropy of 4KB windows for first 64 KB
W = 4096
print("window entropy (first 20 windows of 4KB):")
for i in range(0, min(20 * W, n), W):
    print(f"  0x{i:08x} {i:>9}  {ent(d[i:i+W]):.3f}")
print("last 8 windows:")
for i in range(max(0, n - 8 * W), n, W):
    print(f"  0x{i:08x} {i:>9}  {ent(d[i:i+W]):.3f}")
print("tail bytes:")
for i in range(max(0, n - 128), n, 16):
    row = d[i:i+16]
    print(f"{i:>10} 0x{i:08x} " + ' '.join(f'{b:02x}' for b in row) + '  ' + ''.join(chr(b) if 32 <= b < 127 else '.' for b in row))
