import sys, struct, os, zlib
def load(p):
    d=open(p,'rb').read()
    if d[:4]==b'PACK':
        zf=d.find(b'\x78\xda'); o=zlib.decompressobj(); return o.decompress(d[zf:])+o.flush()
    return d
for p in sys.argv[1:]:
    d=load(p)
    idd=os.path.splitext(p)[0]+'.idd'
    n=os.path.getsize(idd) if os.path.exists(idd) else 0
    print("="*84)
    print(f"{os.path.basename(p)} len={len(d)} idd={n:,}  hdr={struct.unpack_from('<4I',d,0)}")
    zs=[q for q in range(16, len(d)-3) if struct.unpack_from('<I',d,q)[0]==0]
    print("aligned u32==0 at:", [hex(q) for q in zs])
    print("deltas:", [zs[i+1]-zs[i] for i in range(len(zs)-1)])
    # tail candidates: [A][B][0] with B in range
    print("tail candidates (A,B,0) where 17<=B<=idd and A<=idd:")
    for q in zs:
        for back in (8,12):
            r=q-back
            if r<16: continue
            A,B=struct.unpack_from('<2I',d,r)
            if 17<=B<=max(n,17) and A<=max(n,1<<22):
                print(f"   @0x{r:04x} A={A:<9} B={B:<9} C=0   namelen_to_reach={r-16 if r>16 else 0}")
