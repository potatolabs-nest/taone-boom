import sys, collections
p = sys.argv[1]
d = open(p,'rb').read()
print("file", p, "size", len(d))
# autocorrelation to find period
best=[]
for per in range(2, 200):
    same=0; tot=0
    for i in range(len(d)-per):
        tot+=1
        if d[i]==d[i+per]: same+=1
    if tot: best.append((same/tot, per))
best.sort(reverse=True)
print("top periods:", [(round(r,3),p) for r,p in best[:8]])
# find repeats of the 4-byte motif
motif = d[16:20]
print("motif @16:", motif.hex())
offs=[i for i in range(len(d)-4) if d[i:i+4]==motif]
print("motif occurrences:", len(offs), offs[:20])
if len(offs)>1:
    print("deltas:", [offs[i+1]-offs[i] for i in range(min(len(offs)-1,20))])
