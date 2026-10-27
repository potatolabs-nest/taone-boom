import sys, os, math, collections
for path in sys.argv[1:]:
    d=open(path,'rb').read()
    print(f"=== {os.path.basename(path)} ({len(d):,}) ===")
    # entropy in 64KB blocks
    B=65536
    vals=[]
    for i in range(0, min(len(d), B*40), B):
        blk=d[i:i+B]
        c=collections.Counter(blk); n=len(blk)
        e=-sum((v/n)*math.log2(v/n) for v in c.values())
        vals.append(e)
    print("  per-64KB entropy:", " ".join(f"{v:.2f}" for v in vals[:16]))
    print(f"  mean={sum(vals)/len(vals):.3f}  min={min(vals):.3f}  max={max(vals):.3f}")
