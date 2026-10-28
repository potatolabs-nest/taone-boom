import sys, struct, os, json
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')

def stem_tail(name):
    b=name.encode()
    return bytes(b[i]^b[i-4] for i in range(4,len(b)))

def locate(bundle, names):
    idx=open(os.path.join(BOOM,'ndadata',bundle+'.idx'),'rb').read()
    print('==',bundle,'len',len(idx))
    print('  header:', ' '.join(f'{x}' for x in struct.unpack_from('<IIII',idx,0)))
    for nm in names:
        st=stem_tail(nm)
        pos=idx.find(st)
        if pos<0:
            print('  MISS', nm); continue
        start=pos-4   # name begins at pos
        # 4 bytes before stem = len?
        pre=struct.unpack_from('<I',idx,pos-4)[0] if pos>=4 else None
        full_len=len(nm)
        # fields after stem
        foff=pos+len(st)
        fields=struct.unpack_from('<IIII',idx,foff) if foff+16<=len(idx) else None
        print(f'  name@{pos-4:#x} pre4={pre} namelen={full_len} fields@{foff:#x}={fields}  {nm}')

locate('MonWarsRank2nd', ["Quest/KBNB_Quest_MonWarsRankBG.bmp","Quest/KBNB_Quest_MonWarsRankingClose.bmp"])
locate('21thBirthPopUp', ["Quest/c21thBirthPopUp.luc","Quest/KBNB_20221006_21thBirthLobby_Bg.png","Quest/KBNB_20221006_21thBirthLobby_BT01.png"])
