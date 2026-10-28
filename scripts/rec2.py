import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
EXTS=(".bmp",".jpg",".jpeg",".png",".luc",".dds",".ogg",".wav",".txt",".xml",".dat",".ani",".tga",".bik",".slk",".cur",".ico",".scr",".mp3",".ini",".fft")
OK=set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
PFX=("Quest/","PopupEvent/","Game/","Popup/","Event/","Item/","Icon/","Data/","Img/","Effect/","Sound/","Character/","Texture/","Lua/","Cash/","Pet/","Npc/","Ui/")

def dec_full(buf,p,n):
    for pfx in PFX:
        pb=pfx.encode()
        if p+4>len(buf): continue
        seed=bytes(buf[p+i]^pb[i] for i in range(4))
        out=bytearray(); ok=True
        for i in range(n):
            if p+i>=len(buf): ok=False; break
            c=buf[p+i]^(seed[i] if i<4 else out[i-4])
            if c==0 or c<32 or c>126: ok=False; break
            out.append(c)
        if not ok or len(out)<6: continue
        s=out.decode('latin1')
        if s.startswith(pfx) and s.lower().endswith(EXTS) and all(c in OK for c in s) and '//' not in s:
            return s
    return None

def walk(idx):
    """Records from 0x10: [stem][4 ext bytes][4 u32: a,b,c,d], stride=namelen+20."""
    recs=[]
    p=0x10
    n=len(idx)
    while p<n:
        # find namelen: longest run that decrypts to a valid name
        best=None
        for pfx in PFX:
            pb=pfx.encode()
            seed=bytes(idx[p+i]^pb[i] for i in range(4)) if p+4<=n else None
            if seed is None: continue
            out=bytearray(); i=0
            while p+i<n:
                c=idx[p+i]^(seed[i] if i<4 else out[i-4])
                if c==0 or c<32 or c>126: break
                out.append(c); i+=1
            s=out.decode('latin1')
            if s.startswith(pfx) and s.lower().endswith(EXTS) and all(ch in OK for ch in s) and '//' not in s:
                if best is None or len(s)>len(best[0]): best=(s,i)
        if not best: break
        name,clen=best
        ext=idx[p+clen:p+clen+4]
        foff=p+clen+4
        if foff+16>n: break
        a,b,c,d=struct.unpack_from('<IIII',idx,foff)
        recs.append(dict(p=p,clen=clen,name=name,ext=ext,a=a,b=b,c=c,d=d))
        p=foff+16
    return recs

def main(bundles):
    for name in bundles:
        ip=os.path.join(BOOM,'ndadata',name+'.idx')
        if not os.path.exists(ip): continue
        idx=open(ip,'rb').read()
        ds=os.path.getsize(os.path.join(BOOM,'ndadata',name+'.idd'))
        recs=walk(idx)
        end=recs[-1]['p']+recs[-1]['clen']+4+16 if recs else 0x10
        print(f'== {name}: idx={len(idx)} idd={ds} recs={len(recs)} walked_to={end:#x} leftover={len(idx)-end}  sum(b)={sum(r["b"] for r in recs)} sum(a)={sum(r["a"] for r in recs)}')
        for r in recs:
            print(f"  p={r['p']:#06x} clen={r['clen']:3d} ext={r['ext']!r} a={r['a']:9d} b={r['b']:9d} c={r['c']:3d} d={r['d']:5d}  {r['name']}")
if __name__=='__main__':
    main(sys.argv[1:])
