import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
EXTS=(".bmp",".jpg",".jpeg",".png",".luc",".dds",".ogg",".wav",".txt",".xml",".dat",".ani",".tga",".bik",".slk")
OK=set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")

def decrypt_stem(stem):
    for pfx in ("Quest/","PopupEvent/","Game/","Popup/","Event/","Item/","Icon/","Data/","Img/","Effect/","Sound/","Character/","Texture/"):
        pb=pfx.encode()
        if len(pb)>len(stem): continue
        seed=bytes(stem[i]^pb[i] for i in range(4))
        out=bytearray(); bad=False
        for i in range(len(stem)):
            c=stem[i]^(seed[i] if i<4 else out[i-4])
            if c==0: out=out[:i]; break
            if c<32 or c>126: bad=True; break
            out.append(c)
        if bad: continue
        s=out.decode('latin1')
        if s.startswith(pfx) and s.lower().endswith(EXTS) and all(c in OK for c in s) and '//' not in s:
            return s, seed
    return None,None

def parse(idx):
    """Walk records: u32 len | stem[len] | u32 f0 | u32 a | u32 b | u32 zero."""
    recs=[]; p=12; n=len(idx)
    while p+4<=n:
        ln=struct.unpack_from('<I',idx,p)[0]
        if not (4<ln<600) or p+4+ln+16>n: return recs, p
        stem=idx[p+4:p+4+ln]
        nm,seed=decrypt_stem(stem)
        if nm is None: return recs, p
        f0,a,b,c=struct.unpack_from('<IIII',idx,p+4+ln)
        recs.append((p,nm,seed,f0,a,b,c))
        p=p+4+ln+16
    return recs,p

def main(bundles):
    for b in bundles:
        ip=os.path.join(BOOM,'ndadata',b+'.idx')
        dp=os.path.join(BOOM,'ndadata',b+'.idd')
        if not os.path.exists(ip): continue
        idx=open(ip,'rb').read()
        recs,stop=parse(idx)
        dsize=os.path.getsize(dp) if os.path.exists(dp) else 0
        sb=sum(r[5] for r in recs)
        print(f'== {b}: idx={len(idx)} hdr={struct.unpack_from("<III",idx,0)} recs={len(recs)} stop@{stop} idd={dsize} sum(b)={sb} match={sb==dsize}')
        for p,nm,seed,f0,a,bv,c in recs:
            print(f'   @{p:#07x} f0={f0:10d} a={a:9d} b={bv:9d} c={c} {nm}')
if __name__=='__main__':
    main(sys.argv[1:])
