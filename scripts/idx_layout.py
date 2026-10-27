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
    print("="*78)
    print(f"{os.path.basename(p)} len={len(d)} idd={n:,}")
    print("header:", d[:16].hex(' '), struct.unpack_from('<4I',d,0))
    # find adjacent equal u32 pairs, in range
    pairs=[]
    for q in range(16, len(d)-8):
        a,b=struct.unpack_from('<2I', d, q)
        if a==b and 0<a<=max(n,1) and a>16: pairs.append((q,a))
    print(f"equal-adjacent-u32 pairs (in idd range): {len(pairs)}")
    prev=None
    for q,a in pairs:
        gap = q-prev if prev is not None else None
        print(f"   @0x{q:04x} val={a:<9} gap_from_prev={gap}")
        prev=q
