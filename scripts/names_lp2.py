import struct,sys,os
def runs(d):
    """best chain for record = [skip][u32 len][text], varying start & skip"""
    n=len(d); best=(0,0,0,[])
    for start in range(0,64):
        for skip in (0,2,4,6,8):
            i=start; rec=[]; cov=0
            while i+skip+4<=n:
                L=struct.unpack_from('<I',d,i+skip)[0]
                if not (1<=L<=2000): break
                if i+skip+4+L>n: break
                t=d[i+skip+4:i+skip+4+L]
                rec.append((i,L,t)); cov+=skip+4+L
                i=i+skip+4+L
            if len(rec)>best[0]: best=(len(rec),start,skip,rec,cov)
    return best
for p in sys.argv[1:]:
    d=open(p,'rb').read()
    r=runs(d)
    n,start,skip,rec,cov=r[0],r[1],r[2],r[3],r[4]
    print("=== %s size=%d -> recs=%d start=%d skip=%d cov=%d (%.1f%%)"%(
        os.path.basename(p),len(d),n,start,skip,cov,100*cov/len(d)))
    for (i,L,t) in rec[:5]:
        try: s=t.decode('cp949'); k=''
        except: s=t.decode('latin-1'); k=' (non-cp949)'
        print("    @0x%05x L=%-5d %r%s"%(i,L,s[:70],k))
