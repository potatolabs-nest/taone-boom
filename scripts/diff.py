import sys, os, zlib, bz2, lzma
from collections import Counter
A=open(sys.argv[1],'rb').read(); B=open(sys.argv[2],'rb').read()
m=min(len(A),len(B))
print(f"{os.path.basename(sys.argv[1])} {len(A)}  vs  {os.path.basename(sys.argv[2])} {len(B)}")
X=bytes(A[i]^B[i] for i in range(m))
zeros=X.count(0)
print(f"  XOR over {m} bytes: zeros={zeros} ({zeros/m:.4%})")
print(f"  XOR first 64: {X[:64].hex(' ')}")
c=Counter(X); import math
ent=-sum((v/m)*math.log2(v/m) for v in c.values())
print(f"  XOR entropy={ent:.3f} bits/byte  (8.0 = no structure, 0 = identical)")
# compression attempts on each file at several offsets
for name,d in (("A",A),("B",B)):
    for off in (0,4,8,16,20):
        for label,fn in (("zlib",lambda x: zlib.decompressobj().decompress(x)),("bz2",bz2.decompress),("lzma",lzma.decompress)):
            try:
                out=fn(d[off:])
                if len(out)>64: print(f"  {name} @{off} {label}: OK {len(out):,} bytes")
            except Exception: pass
