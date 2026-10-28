import sys, struct, os
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')

def try_len(idx,p):
    """u32 len | stem[len] | a | b | c"""
    if p+4>len(idx): return None
    ln=struct.unpack_from('<I',idx,p)[0]
    if not (0<ln<1024) or p+4+ln+12>len(idx): return None
    stem=idx[p+4:p+4+ln]
    return ln,stem

def dump(bundle):
    idx=open(os.path.join(BOOM,'ndadata',bundle+'.idx'),'rb').read()
    print('==',bundle,'len',len(idx))
    print('  header u32x4:',struct.unpack_from('<IIII',idx,0))
    p=16
    n=0
    while p<len(idx):
        r=try_len(idx,p)
        ok=False
        if r:
            ln,stem=r
            nm=None
            for pfx in ['Quest/','PopupEvent/','Game/']:
                pb=pfx.encode()
                if len(pb)<=len(stem):
                    seed=bytes(stem[i]^pb[i] for i in range(4))
                    out=bytearray(len(stem))
                    for i in range(len(stem)):
                        out[i]=stem[i]^(seed[i] if i<4 else out[i-4])
                    s=out.decode('latin1')
                    if s.startswith(pfx) and ('.' in s) and all(32<=b<127 for b in out):
                        nm=s; break
            if nm:
                a,b,c=struct.unpack_from('<III',idx,p+4+ln)
                print(f'  @{p:#06x} len={ln:4d} a={a:9d} b={b:9d} c={c:4d}  {nm}')
                p=p+4+ln+12; n+=1; ok=True
        if not ok:
            print(f'  @{p:#06x} STOP byte={idx[p]:#04x}')
            break
    print('  records',n)
for b in sys.argv[1:]:
    dump(b)
