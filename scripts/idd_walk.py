import sys, os
from collections import Counter
p = sys.argv[1]
d = open(p,'rb').read()
MAGICS = [b'OggS', b'BM', b'DDS ', b'RIFF', b'PNG\x89', b'\xff\xd8\xff', b'ID3', b'CWS', b'FWS', b'BZh']
pos = []
for m in MAGICS:
    i = 0
    while True:
        i = d.find(m, i)
        if i < 0: break
        pos.append((i, m)); i += 1
pos.sort()
print(f"{os.path.basename(p)} size={len(d):,} payloads={len(pos)}")
print("first 30 payload offsets:")
for i,(o,m) in enumerate(pos[:30]):
    print(f"   {o:>12,}  0x{o:08x}  {m}")
gaps = Counter(pos[i+1][0]-pos[i][0] for i in range(len(pos)-1))
print("most common gaps between consecutive payloads:")
for g,c in gaps.most_common(15):
    print(f"   gap {g:>10,}  x{c}")
# gap mod checks
print("gaps mod 16 counts:", Counter(g%16 for g in gaps.elements() if g<100000).most_common(6))
