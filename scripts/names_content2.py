"""Definitive: is any vh/*.bmp present VERBATIM (whole file) in an archive?"""
import os,sys
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom"
vhd=os.path.join(BOOM,"vh")
targets=[(fn[:-4],open(os.path.join(vhd,fn),'rb').read())
         for fn in sorted(os.listdir(vhd)) if fn.lower().endswith(".bmp")]
hits=0
for root,_,fs in os.walk(BOOM):
    for f in sorted(fs):
        if not f.lower().endswith((".idd",".idx",".pak")): continue
        p=os.path.join(root,f); d=open(p,'rb').read()
        for name,b in targets:
            off=d.find(b)
            if off>=0:
                print("FULL VERBATIM: %-30s %-28s @0x%x (%d B)"%(name,os.path.relpath(p,BOOM),off,len(b)),flush=True)
                hits+=1
        del d
print("full-file hits:",hits)
