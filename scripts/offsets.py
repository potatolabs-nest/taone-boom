import sys, struct, os
from collections import Counter
idx=open(sys.argv[1],'rb').read(); n=os.path.getsize(sys.argv[2])
lim = int(sys.argv[3]) if len(sys.argv)>3 else n
pos=[]
for o in range(16, len(idx)-4):
    v=struct.unpack_from('<I', idx, o)[0]
    if 1000 < v < lim: pos.append((o,v))
print(f"{os.path.basename(sys.argv[1])}: {len(pos)} in-range u32 (limit {lim:,})")
# deltas between consecutive positions
d=Counter(pos[i+1][0]-pos[i][0] for i in range(len(pos)-1))
print("most common positional deltas:", d.most_common(12))
# monotonic runs
run=1; best=1
for i in range(len(pos)-1):
    if pos[i+1][1] > pos[i][1] and pos[i+1][0]-pos[i][0] < 200: run+=1; best=max(best,run)
    else: run=1
print("longest increasing run:", best)
print("first 40 (pos,val):", [(hex(o),hex(v)) for o,v in pos[:40]])
