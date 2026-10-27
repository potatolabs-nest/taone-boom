import sys,struct
path=sys.argv[1]
d=open(path,'rb').read()
print("file",path,"len",len(d),"hdr",d[:16].hex())
n=len(d)
# candidate name-length prefixes: u32 in [4,200], name bytes follow (nonzero-ish)
cands=[]
for i in range(16, n-4):
    v=struct.unpack('<I',d[i:i+4])[0]
    if 4<=v<=200 and i+4+v<=n:
        nm=d[i+4:i+4+v]
        # name-like: mostly printable-ish (not many 0x00)
        if nm.count(0)< max(1,v//8) and b'\x00' not in nm[:min(6,v)]:
            cands.append((i,v))
print("candidates:",len(cands))
prev=None
for i,v in cands[:60]:
    gap = (i-prev) if prev is not None else 0
    print("  @%05x len=%3d gap=%3d name=%s" % (i,v,gap,d[i+4:i+4+v].hex(' ')))
    prev=i
