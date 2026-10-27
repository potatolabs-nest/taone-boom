import sys,struct
path=sys.argv[1]
d=open(path,'rb').read()
n=len(d)
magic=d[:4]; ver=struct.unpack('<I',d[4:8])[0]
n1,n2=struct.unpack('<II',d[8:16])
print("file",path,"len",n,"magic",magic.hex(),"ver",ver,"n1",n1,"n2",n2)
# candidate prefix positions: u32 in [4,200]
pref={}
for i in range(16,n-4):
    v=struct.unpack('<I',d[i:i+4])[0]
    if 4<=v<=200:
        pref[i]=v
# walk: layout [u32 len][name len][tail 16]
i=0x10
recs=[]
def trywalk(start, tail=16, prefixed=True):
    i=start; out=[]
    while i<n:
        if prefixed:
            if i+4>n: break
            L=struct.unpack('<I',d[i:i+4])[0]
            if not (4<=L<=250): return None
            nm=d[i+4:i+4+L]
            if len(nm)<L: return None
            t=i+4+L
        else:
            t=i
        if t+tail>n: break
        out.append((i,t,None,d[t:t+tail]))
        i=t+tail
        if len(out)>n1+50: break
    return out
# hypothesis A: all prefixed from 0x10
for name,start,pf,tail in [("A all-prefixed@0x10",0x10,True,16)]:
    r=trywalk(0x10,16,True)
    print(name, "->", "FAIL" if r is None else len(r))
# find best start & tail by consistency with candidate set
print("--- test: which candidate positions are hit by a prefixed walk with tail T ---")
cands=sorted(pref)
for T in (12,16,20):
    # build walk greedily from first candidate
    start=cands[0]
    r=trywalk(start,T,True)
    print("T=%d from 0x%x -> %s"%(T,start,"FAIL" if r is None else len(r)))
