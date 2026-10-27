import struct,os,collections,math,json,sys
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom/ndadata"
ROOT="/Users/hieu/Workspaces/taone/extracted/Boom"
import re
EXT=r'(?:bmp|dds|tga|png|jpg|jpeg|ani|scr|eff|ogg|tmb|msk|bik)'
NP=re.compile((r'[A-Za-z0-9_./\-]{2,90}?\.'+EXT+r'\b').encode())

def ent(b):
    if not b: return 0
    c=collections.Counter(b); n=len(b)
    return -sum(v/n*math.log2(v/n) for v in c.values())

def load_names():
    out={}
    for f in sorted(os.listdir(BOOM)):
        if f.endswith(".idd"):
            d=open(os.path.join(BOOM,f),'rb').read()
            out[f[:-4]]=sorted(set(m.group(0).decode('latin-1') for m in NP.finditer(d)))
    # whole-archive corpus too
    return out

nm=load_names()
# global corpus = all unique names across all idds
corpus=set()
for v in nm.values(): corpus|=set(v)
print("corpus size",len(corpus))
# focus on bundles whose idd name-set is small & complete
for stem in ("TwoDayFlow01","SelectCandy","FindNote"):
    ix=os.path.join(BOOM,stem+".idx")
    if not os.path.exists(ix): continue
    d=open(ix,'rb').read()
    names=[n for n in nm[stem]]
    print("\n=== %s idx=%d names=%d"%(stem,len(d),len(names)))
    for name in names[:3]:
        pb=name.encode()
        best=[]
        for off in range(0x10,len(d)-len(pb)):
            w=d[off:off+len(pb)]
            x=bytes(a^b for a,b in zip(w,pb))
            best.append((ent(x),off,x))
        best.sort()
        e,off,x=best[0]
        print("  name=%-45s bestoff=0x%03x H(xor)=%.2f  xor=%s"%(name,off,e,x[:32].hex(' ')))
        # periodic check
        for per in (1,2,4,8,16,20):
            sc=sum(1 for i in range(len(x)) if x[i]==x[i%per])/len(x)
            if sc>0.5: print("      period %d match %.0f%%"%(per,100*sc))
