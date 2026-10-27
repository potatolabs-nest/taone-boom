import struct,sys,os
def walk(d,start,skip):
    i=start; rec=[]; n=len(d)
    while i+skip+4<=n:
        L=struct.unpack_from('<I',d,i+skip)[0]
        if not (1<=L<=4000): break
        if i+skip+4+L>n: break
        key=struct.unpack_from('<H',d,i)[0] if skip>=2 else None
        rec.append((i,key,L,d[i+skip+4:i+skip+4+L]))
        i+=skip+4+L
    return rec
for p in sys.argv[1:]:
    d=open(p,'rb').read()
    best=None
    for start in range(0,16):
        for skip in (2,4,6,8):
            r=walk(d,start,skip); cov=sum(skip+4+len(t) for _,_,_,t in r) if r else 0
            if best is None or cov>best[3]: best=(start,skip,len(r),cov,r)
    start,skip,n,cov,r=best
    print("=== %s size=%d start=%d skip=%d recs=%d cov=%d (%.1f%%)"%(os.path.basename(p),len(d),start,skip,n,cov,100*cov/len(d)))
    keys=[k for _,k,_,_ in r if k is not None]
    if keys:
        print("    keys first10:",keys[:10]," monotonic:",all(keys[i]<keys[i+1] for i in range(min(20,len(keys))-1)))
    for (i,k,L,t) in r[:3]:
        try: s=t.decode('cp949')
        except: s=t.decode('latin-1')
        print("    @0x%05x key=%s L=%-4d %r"%(i,k,L,s[:55]))
