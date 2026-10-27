import struct,sys,os
p=sys.argv[1]
d=open(p,'rb').read()
print("file",p,"size",len(d))
print("magic",d[:4].hex(),"ver",struct.unpack_from('<I',d,4)[0],
      "c8",struct.unpack_from('<I',d,8)[0],"c12",struct.unpack_from('<I',d,12)[0])
def vis(b): return ''.join(chr(c) if 32<=c<127 else '.' for c in b)
# brute force: at 0x10, try u32 len @0x10 (i.e. name starts 0x14) chain
for name_off in (0x10,0x14):
    i=name_off; recs=[]; ok=True
    while i+12<=len(d) and len(recs)<8:
        if name_off==0x14:
            L=struct.unpack_from('<I',d,i-4)[0]
        else:
            L=struct.unpack_from('<I',d,i-4)[0] if i>=4 else None
        L=struct.unpack_from('<I',d,i-4)[0]
        if not (1<=L<=300): ok=False; break
        nm=d[i:i+L]; a,b,c=struct.unpack_from('<III',d,i+L)
        recs.append((i-4,L,nm,a,b,c)); i=i+L+12
    print("--- name_off 0x%x ok=%s recs=%d"%(name_off,ok,len(recs)))
    for (o,L,nm,a,b,c) in recs:
        print("  @0x%04x L=%-3d |%s| a=%d b=%d c=%d"%(o,L,vis(nm),a,b,c))
