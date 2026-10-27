import sys, struct, os
from collections import Counter
p, idd = sys.argv[1], sys.argv[2]
d = open(p,'rb').read(); n = os.path.getsize(idd)
print(f"=== {os.path.basename(p)}  idx={len(d)}  idd={n:,}")
# Find (v,v) adjacent-equal u32 pairs anywhere
pairs = []
for q in range(16, len(d)-8):
    a = struct.unpack_from('<I', d, q)[0]
    b = struct.unpack_from('<I', d, q+4)[0]
    if a == b and 0 < a < n:
        pairs.append((q, a))
print(f"adjacent-equal u32 pairs: {len(pairs)}")
if pairs:
    vals = [v for _, v in pairs]
    print(f"  value range: {min(vals):,} .. {max(vals):,}")
    print(f"  SUM of values = {sum(vals):,}   (idd size = {n:,})")
    print(f"  sum/idd = {sum(vals)/n:.4f}   <-- near 1.0 would mean these ARE the sizes")
    print(f"  positions spacing: {Counter((pairs[i+1][0]-pairs[i][0]) for i in range(len(pairs)-1)).most_common(6)}")
    print(f"  first 12: {[(hex(q),v) for q,v in pairs[:12]]}")
