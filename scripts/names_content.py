"""Do the 34 vh BMPs appear verbatim in any archive? Cheap bytes.find, no index."""
import os
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom"
vhd=os.path.join(BOOM,"vh")
targets=[]
for fn in sorted(os.listdir(vhd)):
    if fn.lower().endswith(".bmp"):
        b=open(os.path.join(vhd,fn),'rb').read()
        if len(b)>=64: targets.append((fn[:-4],b))
hits=[]
for root,_,fs in os.walk(BOOM):
    for f in fs:
        if not f.lower().endswith((".idd",".idx",".pak")): continue
        p=os.path.join(root,f); d=open(p,'rb').read()
        rel=os.path.relpath(p,BOOM)
        for name,b in targets:
            probe=b[len(b)//3:len(b)//3+48]
            off=d.find(probe)
            if off>=0:
                hits.append((name,rel,off,len(b)))
                print("HIT %-34s %-32s @0x%x"%(name,rel,off),flush=True)
        del d
print("done hits=%d"%len(hits))
