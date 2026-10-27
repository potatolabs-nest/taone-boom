import sys, struct
from collections import Counter
for p in sys.argv[1:]:
    d=open(p,'rb').read()
    print("="*70); print(p, "size", len(d))
    print("header:", d[:64].hex(' '))
    # autocorr
    best=[]
    for per in range(4, 400):
        n=len(d)-per
        if n<200: break
        same=sum(1 for i in range(n) if d[i]==d[i+per])
        best.append((same/n, per))
    best.sort(reverse=True)
    print("top periods:", [(round(r,3),q) for r,q in best[:5]])
    per = best[0][1]
    print("stride candidate", per, "-> count ~", len(d)//per, "remainder", len(d)%per)
    # try to read first ints
    print("first 16 u32:", struct.unpack('<16I', d[:64]))
