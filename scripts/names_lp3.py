import struct,sys,os,collections
def best_chain(d,minlen=1,maxlen=4000):
    n=len(d); best=(0,0,0,0)  # recs,start,skip,cov
    for start in range(0,64):
        for skip in (0,1,2,3,4,6,8):
            i=start; cnt=0; cov=0
            while i+skip+4<=n:
                L=struct.unpack_from('<I',d,i+skip)[0]
                if not (minlen<=L<=maxlen): break
                if i+skip+4+L>n: break
                cnt+=1; cov+=skip+4+L; i+=skip+4+L
            if cov>best[3]: best=(cnt,start,skip,cov)
    return best
def decode(t):
    try: return t.decode('cp949'),'cp949'
    except: 
        try: return t.decode('ascii'),'ascii'
        except: return t.decode('latin-1'),'lat1'
for p in sys.argv[1:]:
    d=open(p,'rb').read()
    cnt,start,skip,cov=best_chain(d)
    print("=== %s size=%d -> recs=%d start=%d skip=%d cov=%d (%.1f%%)"%(os.path.basename(p),len(d),cnt,start,skip,cov,100*cov/len(d)))
    i=start; shown=0
    while i+skip+4<=len(d) and shown<4:
        L=struct.unpack_from('<I',d,i+skip)[0]
        if not (1<=L<=4000) or i+skip+4+L>len(d): break
        s,enc=decode(d[i+skip+4:i+skip+4+L])
        print("    @0x%05x L=%-5d [%s] %r"%(i,L,enc,s[:60]))
        i+=skip+4+L; shown+=1
