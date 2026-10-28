import sys, struct, os, zlib
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')
recs={
 'MonWarsRank2nd':[
  ('Quest/cMonWarsRank2nd.luc',7631,7631),
  ('Quest/KBNB_Quest_MonWarsRankBG.bmp',415816,411015),
  ('Quest/KBNB_Quest_MonWarsRankingClose.bmp',423862,5344)],
 '21thBirthPopUp':[
  ('Quest/c21thBirthPopUp.luc',8713,9700),
  ('Quest/KBNB_20221006_21thBirthLobby_Bg.png',534735,525598),
  ('Quest/KBNB_20221006_21thBirthLobby_BT01.png',548559,27680),
  ('Quest/KBNB_20221006_21thBirthLobby_BT02.png',568524,13251),
  ('Quest/KBNB_20221006_21thBirthLobby_LB_Bt.bmp',704327,127359)],
}
for b,pairs in recs.items():
    d=open(os.path.join(BOOM,'ndadata',b+'.idd'),'rb').read()
    print('==',b,'idd',len(d),'sum(b)=',sum(x[2] for x in pairs))
    for nm,a,bb in pairs:
        print(f'  {nm}')
        print(f'    a={a} b={bb}  a+b={a+bb}  size-a={len(d)-a}')
        print(f'    @a     {d[a:a+12].hex(" ")}')
        print(f'    @a-b   {d[a-bb if a-bb>=0 else 0:a-bb+12 if a-bb>=0 else 12].hex(" ")}')
        # try zlib at a
        for off,tag in [(a,'a'),(len(d)-bb,'len-b'),(a-bb,'a-b')]:
            if 0<=off<len(d):
                try:
                    z=zlib.decompressobj()
                    out=z.decompress(d[off:off+200000])
                    print(f'    zlib@{off}({tag}) -> {len(out)} bytes consumed? unused={len(z.unused_data)}')
                except Exception as e:
                    print(f'    zlib@{off}({tag}) FAIL {e}')
