import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
DIRS=["Quest/","PopupEvent/","Game/","Popup/","Event/","Item/","Icon/"]
EXTS=(".bmp",".jpg",".jpeg",".png",".luc",".dds",".ogg",".wav",".txt",".xml",".dat")

def decrypt(stem,seed):
    out=bytearray(len(stem))
    for i in range(len(stem)):
        out[i]=stem[i]^(seed[i] if i<4 else out[i-4])
    return bytes(out)

def best(stem):
    for pfx in DIRS:
        pb=pfx.encode()
        if len(pb)>len(stem): continue
        seed=bytes(stem[i]^pb[i] for i in range(4))
        nm=decrypt(stem,seed)
        if not all(32<=b<127 for b in nm): continue
        s=nm.decode('latin1')
        if s.startswith(pfx) and s.lower().endswith(EXTS) and '//' not in s:
            return s
    return None

def scan(bundle):
    idx=open(os.path.join(BOOM,'ndadata',bundle+'.idx'),'rb').read()
    print('==',bundle,'len',len(idx))
    print('  hdr:',struct.unpack_from('<IIII',idx,0))
    hits=[]
    for p in range(0,len(idx)-4):
        ln=struct.unpack_from('<I',idx,p)[0]
        if 0<ln<1024 and p+4+ln+12<=len(idx):
            s=best(idx[p+4:p+4+ln])
            if s: hits.append((p,ln,s))
    for p,ln,s in hits:
        a,b,c=struct.unpack_from('<III',idx,p+4+ln)
        print(f'  @{p:#06x} len={ln:4d} f={a:10d}/{b:10d}/{c} {s}')
    print('  hits',len(hits))
for b in sys.argv[1:]:
    scan(b)
