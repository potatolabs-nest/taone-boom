import sys, struct, os
from collections import Counter

idx_path, idd_path = sys.argv[1], sys.argv[2]
idx = open(idx_path,'rb').read()
idd = open(idd_path,'rb').read()
print(f"{os.path.basename(idx_path)} idx={len(idx)} idd={len(idd)}")
magic, ver, a, b = struct.unpack_from('<IIII', idx, 0)
print(f"  magic={magic:#x} ver={ver} f1={a} f2={b}")

MAGICS = [b'OggS', b'BM', b'DDS ', b'RIFF', b'PNG', b'\xff\xd8\xff', b'ID3', b'CWS', b'FWS']

# For each byte position in the sorted region, count how often a u32 there
# is a valid offset into the idd whose target starts with a known magic.
pos_hits = Counter()
for off in range(0, min(len(idx)-8, 4000)):
    v = struct.unpack_from('<I', idx, off)[0]
    if 0 < v < len(idd)-4:
        for m in MAGICS:
            if idd[v:v+len(m)] == m:
                pos_hits[off] += 1
                break
print("  byte positions whose u32 points at a magic:", pos_hits.most_common(12))

# Where do records start? look at periodicity of hits
hits = sorted(pos_hits)
if hits:
    print("  deltas between hit positions:", Counter(hits[i+1]-hits[i] for i in range(len(hits)-1)).most_common(8))
