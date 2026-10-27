import sys, struct, os
idx = open(sys.argv[1],'rb').read(); idd = open(sys.argv[2],'rb').read()
n = len(idd)
print(f"{os.path.basename(sys.argv[1])} idx={len(idx)} idd={n:,}")
res=[]
for S in range(24, 90):
    for F in range(0, S):
        p = 16 + F; vals=[]
        while p+4 <= len(idx):
            vals.append(struct.unpack_from('<I', idx, p)[0]); p += S
        if len(vals) < 100: continue
        inc = sum(1 for i in range(len(vals)-1) if vals[i] < vals[i+1])
        rng = sum(1 for v in vals if 0 <= v < n)
        r = (inc/(len(vals)-1)) * (rng/len(vals))
        if r > 0.9: res.append((r, S, F, len(vals), vals[:6]))
res.sort(reverse=True)
for r,S,F,c,v in res[:12]:
    print(f"  score={r:.3f} stride={S:>3} fieldoff={F:>3} n={c:>6} first={v}")
if not res: print("  no monotonic in-range u32 field found")
