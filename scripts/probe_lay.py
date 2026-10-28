import sys, struct, os
sys.path.insert(0,'/Users/hieu/Workspaces/taone/scripts')
import idx_decrypt as D
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')

def dump(bundle):
    idx=open(os.path.join(BOOM,'ndadata',bundle+'.idx'),'rb').read()
    print('==',bundle,'idx',len(idx))
    print(' head:', idx[:16].hex(' '))
    print(' @8 u32:', struct.unpack_from('<I',idx,8)[0], ' @12:', struct.unpack_from('<I',idx,12)[0])
    p=16; i=0
    while p+4<=len(idx):
        ln=struct.unpack_from('<I',idx,p)[0]
        if 0<ln<1024 and p+4+ln<=len(idx):
            stem=idx[p+4:p+4+ln]
            nm,seed=D.best_name(stem)
            if nm:
                rest=idx[p+4+ln:p+4+ln+16]
                vals=struct.unpack('<IIII',rest) if len(rest)==16 else None
                print(f'  rec{i} @0x{p:x} len={ln} seed={seed.hex()} {nm.decode()}')
                print(f'      fields={vals}')
                i+=1
                p=p+4+ln+16
                continue
        p+=1
    print('  records:',i)

for b in sys.argv[1:]:
    dump(b)
