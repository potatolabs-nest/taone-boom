import sys,struct,collections
def score(b):
    if 97<=b<=122: return 4.0      # a-z
    if 48<=b<=57: return 3.0       # 0-9
    if b in (46,95,47,92): return 3.5  # . _ / \
    if 65<=b<=90: return 1.0       # A-Z
    if b==32: return 0.5
    if 32<=b<127: return 0.3
    return -4.0
def parse(path,start,tailn):
    d=open(path,'rb').read(); n=len(d); i=start; recs=[]
    while i+4+tailn<=n:
        L=struct.unpack('<I',d[i:i+4])[0]
        if not(1<=L<=250): break
        if i+4+L+tailn>n: break
        recs.append(d[i+4:i+4+L]); i=i+4+L+tailn
    return recs
path=sys.argv[1]; start=int(sys.argv[2],16) if len(sys.argv)>2 else 0x37
tailn=int(sys.argv[3]) if len(sys.argv)>3 else 16
recs=parse(path,start,tailn)
print(path.split('/')[-1],"recs",len(recs),"avglen",sum(map(len,recs))/len(recs))
for P in range(1,17):
    key=[0]*P
    for j in range(P):
        best=None
        for k in range(256):
            s=sum(score(nm[j]^k) for nm in recs if len(nm)>j)
            if best is None or s>best[0]: best=(s,k)
        key[j]=best[1]
    # decrypt all
    good=0; tot=0; names=[]
    for nm in recs:
        out=bytes(b^key[i%P] for i,b in enumerate(nm))
        names.append(out)
        for b in out:
            tot+=1; good+= (1 if score(b)>=0.5 else 0)
    print("P=%2d key=%-32s printable=%.3f  ex:%s"%(P,bytes(key).hex(),
        good/tot,''.join(chr(b) if 32<=b<127 else '.' for b in names[0])[:40]))
