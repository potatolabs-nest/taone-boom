import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
EXTS=(".bmp",".jpg",".jpeg",".png",".luc",".dds",".ogg",".wav",".txt",".xml",".dat",".ani",".tga",".bik",".slk")
OK=set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")

def decrypt_at(idx,p,pfx,maxlen=300):
    """Decrypt starting at idx[p], assuming plaintext starts with pfx."""
    pb=pfx.encode()
    if p+4>len(idx): return None
    seed=bytes(idx[p+i]^pb[i] for i in range(4))
    out=bytearray()
    for i in range(maxlen):
        if p+i>=len(idx): break
        s=idx[p+i]
        c=s^(seed[i] if i<4 else out[i-4])
        if c<32 or c>126: break   # NUL terminator or junk
        out.append(c)
    s=out.decode('latin1')
    return s,seed

def find_names(idx):
    res=[]
    for p in range(16,len(idx)):
        for pfx in ("Quest/","PopupEvent/","Game/","Popup/"):
            r=decrypt_at(idx,p,pfx)
            if not r: continue
            s,seed=r
            if len(s)<8: continue
            if not s.startswith(pfx): continue
            if any(c not in OK for c in s): continue
            if not s.lower().endswith(EXTS): continue
            res.append((p,s,seed))
            break
    # dedupe: keep longest name per start offset
    return res

def main(paths):
    for path in paths:
        name=os.path.splitext(os.path.basename(path))[0]
        idx=open(path,'rb').read()
        print(f'== {name}  idx={len(idx)}')
        res=find_names(idx)
        for p,s,seed in res:
            print(f'  @{p:#06x} seed={seed.hex(" ")} {s}')
        print(f'  total {len(res)}')
if __name__=='__main__':
    main(sys.argv[1:])
