import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
EXTS=(".bmp",".jpg",".jpeg",".png",".luc",".dds",".ogg",".wav",".txt",".xml",".dat",".ani",".tga",".bik",".slk")
OK=set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
PFX=("Quest/","PopupEvent/","Game/","Popup/","Event/","Item/","Icon/","Data/","Img/","Effect/","Sound/","Character/","Texture/","Lua/","Cash/","Pet/")

def decrypt(stem,pfx):
    pb=pfx.encode()
    if len(pb)>len(stem): return None
    seed=bytes(stem[i]^pb[i] for i in range(4))
    out=bytearray()
    for i in range(len(stem)):
        c=stem[i]^(seed[i] if i<4 else out[i-4])
        if c==0: break
        if c<32 or c>126: return None
        out.append(c)
    s=out.decode('latin1')
    if not s.startswith(pfx): return None
    if not s.lower().endswith(EXTS): return None
    if any(c not in OK for c in s) or '//' in s: return None
    return s,seed

def name_at(stem):
    for pfx in PFX:
        r=decrypt(stem,pfx)
        if r: return r
    return None,None

def parse(idx,start=8,trace=False):
    recs=[]
    n=len(idx)
    p=start
    while p+4<n:
        ln=struct.unpack_from('<I',idx,p)[0]
        if 4<ln<600 and p+4+ln+16<=n:
            nm,seed=name_at(idx[p+4:p+4+ln])
            if nm:
                x,a,b,c=struct.unpack_from('<IIII',idx,p+4+ln)
                recs.append(dict(pre=p,nlen=ln,name=nm,a=a,b=b,c=c,seed=seed.hex()))
                p=p+4+ln+16
                continue
        p+=1
        if trace: print(f'   skip @{p-1:#x}')
    return recs

def main(bundles,trace=False):
    for name in bundles:
        idxp=os.path.join(BOOM,'ndadata',name+'.idx')
        iddp=os.path.join(BOOM,'ndadata',name+'.idd')
        if not os.path.exists(idxp): continue
        idx=open(idxp,'rb').read()
        recs=parse(idx,trace=trace)
        dsize=os.path.getsize(iddp) if os.path.exists(iddp) else 0
        sb=sum(r['b'] for r in recs)
        print(f'== {name}: recs={len(recs)} idx={len(idx)} idd={dsize} sum(b)={sb} diff_idd-sum={dsize-sb} hdr@8={struct.unpack_from("<I",idx,8)[0]}')
        for r in recs:
            print(f"   pre={r['pre']:#07x} nlen={r['nlen']:3d} a={r['a']:9d} b={r['b']:9d} c={r['c']:4d}  {r['name']}")
if __name__=='__main__':
    main(sys.argv[1:])
