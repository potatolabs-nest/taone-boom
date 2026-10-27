import sys, struct, os
from collections import Counter
idx_p, idd_p = sys.argv[1], sys.argv[2]
idx = open(idx_p,'rb').read(); idd = open(idd_p,'rb').read()
MAGICS=[b'OggS',b'BM',b'DDS ',b'RIFF',b'PNG\x89',b'\xff\xd8\xff',b'ID3',b'CWS',b'FWS',b'BZh']

best=[]
for P in range(16, 64):
    for S in range(32, 52):
        # collect u32 candidates
        vals=[]
        p=P
        while p+4 <= len(idx):
            v=struct.unpack_from('<I', idx, p)[0]
            vals.append(v); p+=S
        if len(vals)<50: continue
        # strictly increasing?
        if any(vals[i]>=vals[i+1] for i in range(min(len(vals)-1,400))): continue
        if not (0 < vals[0] < len(idd)): continue
        if vals[-1] > len(idd)+64: continue
        # check cumulative ends land on magics (end of entry i = start of i+1)
        hits=0; tot=0
        for v in vals[:600]:
            if 0 < v < len(idd)-8:
                tot+=1
                if any(idd[v:v+len(m)]==m for m in MAGICS): hits+=1
        if tot: best.append((hits/tot, hits, tot, P, S, len(vals), vals[:4]))
best.sort(reverse=True)
for r in best[:10]:
    print(f"rate={r[0]:.3f} hits={r[1]}/{r[2]} phase={r[3]} stride={r[4]} n={r[5]} first={r[6]}")
