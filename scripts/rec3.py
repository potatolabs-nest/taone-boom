import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
EXTS=(".bmp",".jpg",".jpeg",".png",".luc",".dds",".ogg",".wav",".txt",".xml",".dat",".ani",".tga",".bik",".slk",".cur",".ico",".scr",".mp3",".ini",".fft",".act")
OK=set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
PFX=("Quest/","PopupEvent/","Game/","Popup/","Event/","Item/","Icon/","Data/","Img/","Effect/","Sound/","Character/","Texture/","Lua/","Cash/","Pet/","Npc/","Ui/","UI/","Quest/")

def decode_name(buf,p):
    """Decode a stem at buf[p]; return (name, crypto_len) where crypto_len is
    the number of encrypted bytes consumed (excluding any trailing NUL)."""
    for pfx in PFX:
        pb=pfx.encode()
        if len(pb)<4 or p+4>len(buf): continue
        seed=bytes(buf[p+i]^pb[i] for i in range(4))
        out=bytearray(); i=0
        while p+i<len(buf):
            c=buf[p+i]^(seed[i] if i<4 else out[i-4])
            if c==0 or c<32 or c>126: break
            out.append(c); i+=1
        s=out.decode('latin1')
        if s.startswith(pfx) and s.lower().endswith(EXTS) and all(ch in OK for ch in s) and '//' not in s:
            return s,i
    return None,0

def walk(idx):
    recs=[]
    n=len(idx)
    p=0x10
    first=True
    while p<n:
        # optional u32 length prefix
        if not first:
            ln=struct.unpack_from('<I',idx,p)[0] if p+4<=n else 0
            nm,cl=decode_name(idx,p+4) if 0<ln<600 else (None,0)
            if nm and cl==ln:
                p+=4
            else:
                nm,cl=decode_name(idx,p)
        else:
            nm,cl=decode_name(idx,p)
        if not nm: return recs,p
        ext=idx[p+cl:p+cl+4]
        fo=p+cl+4
        if fo+12>n: return recs,p
        a,b,c=struct.unpack_from('<III',idx,fo)
        recs.append(dict(p=p,cl=cl,name=nm,ext=ext,a=a,b=b,c=c))
        p=fo+12
        first=False
    return recs,p

def main(bundles):
    for name in bundles:
        ip=os.path.join(BOOM,'ndadata',name+'.idx')
        if not os.path.exists(ip): continue
        idx=open(ip,'rb').read()
        dp=os.path.join(BOOM,'ndadata',name+'.idd')
        ds=os.path.getsize(dp) if os.path.exists(dp) else 0
        recs,stop=walk(idx)
        print(f'== {name}: idx={len(idx)} idd={ds} recs={len(recs)} stop={stop:#x} leftover={len(idx)-stop} sum(a)={sum(r["a"] for r in recs)} sum(b)={sum(r["b"] for r in recs)} sum(c)={sum(r["c"] for r in recs)}')
        for r in recs:
            print(f"  p={r['p']:#06x} cl={r['cl']:3d} ext={r['ext'].decode('latin1')} a={r['a']:9d} b={r['b']:9d} c={r['c']:3d}  {r['name']}{r['ext'].decode('latin1')}")
if __name__=='__main__':
    main(sys.argv[1:])
