import sys, struct, os
idx_p, idd_p = sys.argv[1], sys.argv[2]
idx=open(idx_p,'rb').read(); idd=open(idd_p,'rb').read()
MAGICS=[b'OggS',b'BM',b'DDS ',b'RIFF',b'PNG\x89',b'\xff\xd8\xff',b'ID3',b'CWS',b'FWS',b'BZh',b'KTX ',b'BC\x00']
starts=set()
for m in MAGICS:
    i=0
    while True:
        i=idd.find(m,i)
        if i<0: break
        starts.add(i); i+=1
print(f"{os.path.basename(idd_p)}: {len(starts):,} payload start positions")
# stride via autocorrelation on idx
best=[]
for per in range(8, 200):
    n=len(idx)-per
    if n<100: break
    same=sum(1 for i in range(n) if idx[i]==idx[i+per])
    best.append((same/n, per))
best.sort(reverse=True)
print("idx top periods:", [(round(r,3),p) for r,p in best[:6]])
results=[]
for P in range(8, 80):
    for S in range(8, 64):
        vals=[]; p=P
        while p+4<=len(idx):
            vals.append(struct.unpack_from('<I', idx, p)[0]); p+=S
        if len(vals)<30: continue
        hit=sum(1 for v in vals if v in starts)
        if hit: results.append((hit/len(vals), hit, len(vals), P, S))
results.sort(reverse=True)
print("best (P,S) by fraction of u32 that are payload starts:")
for r in results[:12]:
    print(f"  rate={r[0]:.4f} hits={r[1]}/{r[2]} phase={r[3]} stride={r[4]}")
if not results: print("  none — no u32 field aligns with payload starts")
