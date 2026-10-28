import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
EXTS=(".bmp",".jpg",".jpeg",".png",".luc",".dds",".ogg",".wav",".txt",".xml",".dat",".ani",".tga",".bik",".slk",".cur",".ico",".scr",".mp3",".ini",".fft",".act",".spr",".img")
OK=set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
PFX=("Quest/","PopupEvent/","Game/","Popup/","Event/","Item/","Icon/","Data/","Img/","Effect/","Sound/","Character/","Texture/","Lua/","Cash/","Pet/","Npc/","Ui/","UI/")

def dec_name(buf,p,maxlen=400):
    best=None
    for pfx in PFX:
        pb=pfx.encode()
        if len(pb)<4 or p+4>len(buf): continue
        seed=bytes(buf[p+i]^pb[i] for i in range(4))
        out=bytearray(); i=0
        while p+i<len(buf) and i<maxlen:
            c=buf[p+i]^(seed[i] if i<4 else out[i-4])
            if c==0 or c<32 or c>126: break
            out.append(c); i+=1
        s=out.decode('latin1')
        if s.startswith(pfx) and s.lower().endswith(EXTS) and all(ch in OK for ch in s) and '//' not in s:
            if best is None or len(s)>len(best[0]): best=(s,i)
    return best

def walk(idx):
    recs=[]; p=0x10; n=len(idx)
    while p<n:
        r=dec_name(idx,p)
        if not r: break
        nm,L=r
        ext=idx[p+L:p+L+4]
        fo=p+L+4
        if fo+12>n: break
        a,b,c=struct.unpack_from('<III',idx,fo)
        recs.append(dict(p=p,L=L,name=nm,ext=ext.decode('latin1','replace'),a=a,b=b,c=c))
        p=fo+12
    return recs,p

def main(names,verbose=False):
    tot=0
    for name in names:
        ip=os.path.join(BOOM,'ndadata',name+'.idx')
        if not os.path.exists(ip): continue
        idx=open(ip,'rb').read()
        dp=os.path.join(BOOM,'ndadata',name+'.idd')
        ds=os.path.getsize(dp) if os.path.exists(dp) else 0
        recs,stop=walk(idx)
        sb=sum(r['b'] for r in recs); sa=sum(r['a'] for r in recs)
        flag='OK' if sb==ds else 'DIFF'
        print(f'{name:38s} recs={len(recs):3d} idx={len(idx):6d} idd={ds:9d} sum_b={sb:9d} [{flag} {ds-sb:+}] stop={stop:#06x}/{len(idx):#06x}')
        if verbose:
            cum=0
            for r in recs:
                print(f"   p={r['p']:#06x} L={r['L']:3d} ext={r['ext']} a={r['a']:9d} b={r['b']:9d} c={r['c']:3d} cum=[{cum},{cum+r['b']})  {r['name']}")
                cum+=r['b']
        tot+=len(recs)
    print('total records',tot)

if __name__=='__main__':
    import glob
    args=sys.argv[1:]
    v='-v' in args
    args=[a for a in args if a!='-v']
    if not args:
        args=sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(BOOM,'ndadata','*.idx')))
    main(args,v)
