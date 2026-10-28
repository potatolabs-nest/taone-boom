import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
EXTS=(".bmp",".jpg",".jpeg",".png",".luc",".dds",".ogg",".wav",".txt",".xml",".dat",".ani",".tga",".bik",".slk",".cur",".ico",".scr",".mp3",".ini",".fft",".act")
OK=set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
PFX=("Quest/","PopupEvent/","Game/","Popup/","Event/","Item/","Icon/","Data/","Img/","Effect/","Sound/","Character/","Texture/","Lua/","Cash/","Pet/","Npc/","Ui/","UI/")

def dec_at(buf,p):
    best=None
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
            if best is None or len(s)>len(best[0]): best=(s,i)
    return best

def solve(name):
    idx=open(os.path.join(BOOM,'ndadata',name+'.idx'),'rb').read()
    idd=os.path.join(BOOM,'ndadata',name+'.idd')
    ds=os.path.getsize(idd) if os.path.exists(idd) else 0
    n=len(idx)
    # find all name positions
    pos=[]
    p=0
    while p<n:
        r=dec_at(idx,p)
        if r: pos.append((p,r[0],r[1]))
        p+=1
    # dedupe overlapping: keep the one with longest name at each start, drop starts inside a previous name
    print(f'== {name} idx={n} idd={ds} raw_pos={len(pos)}')
    for p,nm,L in pos:
        # try field positions
        cands={}
        for label,fo in [('+4+L',p+4+L),('+L',p+L),('+4+L+4',p+4+L+4),('-4+L',p-4+L) ]:
            if fo+12<=n:
                a,b,c=struct.unpack_from('<III',idx,fo)
                cands[label]=(a,b,c)
        print(f'  @{p:#06x} L={L:3d} {nm}')
        for k,v in cands.items():
            print(f'       {k}: {v}')
if __name__=='__main__':
    for x in sys.argv[1:]: solve(x)
