import struct,sys,os
def vis(b): return ''.join(chr(c) if 32<=c<127 else '.' for c in b)
def chain(d,start,psz,maxL=256):
    i=start; out=[]; n=len(d)
    while i+psz+12<=n:
        if psz==4: L=struct.unpack_from('<I',d,i)[0]
        else:      L=struct.unpack_from('<H',d,i)[0]
        if not (1<=L<=maxL): return out,False
        if i+psz+L+12>n: return out,False
        nm=d[i+psz:i+psz+L]
        a,b,c=struct.unpack_from('<III',d,i+psz+L)
        out.append((i,L,nm,a,b,c)); i+=psz+L+12
    return out,True
for p in sys.argv[1:]:
    d=open(p,'rb').read()
    best=None
    for start in range(0x0c,0x60):
        for psz in (4,2):
            rs,done=chain(d,start,psz)
            ab=sum(1 for r in rs if r[3]==r[4] and r[5]==0)
            score=(done,len(rs),ab)
            if best is None or score>best[0]: best=(score,start,psz,rs)
    (score,start,psz,rs)=best
    print("=== %s size=%d  BEST start=0x%x psz=%d recs=%d filled=%s"%(os.path.basename(p),len(d),start,psz,len(rs),score))
    for (o,L,nm,a,b,c) in rs[:8]:
        print("   @0x%05x L=%-3d |%-32s| a=%-10d b=%-10d c=%d"%(o,L,vis(nm),a,b,c))
    # entropy of cols over all recs
    import collections,math
    if len(rs)>20:
        W=min(r[1] for r in rs)
        print("   min len",W,"  cols:", " ".join(
            "%.2f"%(-sum(v/len([1 for r in rs if r[1]>j])*math.log2(v/len([1 for r in rs if r[1]>j])) for v in collections.Counter([r[2][j] for r in rs if r[1]>j]).values()))
            for j in range(min(W,20))))
