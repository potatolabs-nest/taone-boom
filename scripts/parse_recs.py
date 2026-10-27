import sys, struct, os
d=open(sys.argv[1],'rb').read()
magic=d[:4]; ver=struct.unpack_from('<I',d,4)[0]
f1,f2=struct.unpack_from('<II',d,8)
print(f"{os.path.basename(sys.argv[1])} len={len(d)} magic={magic.hex()} ver={ver} f1={f1} f2={f2}")
p=16; i=0
while p+4<=len(d) and i<14:
    L=struct.unpack_from('<I',d,p)[0]
    print(f"\nrec {i}: @0x{p:04x} len_u32={L}")
    if not (0<L<300) or p+4+L>len(d):
        print("   implausible length, stop"); break
    nm=d[p+4:p+4+L]
    print(f"   name[{L}] = {nm!r}")
    print(f"   name hex = {nm.hex(' ')}")
    after=p+4+L
    print(f"   next 16 bytes @0x{after:04x}: {d[after:after+16].hex(' ')}")
    u=struct.unpack_from('<4I', d, after) if after+16<=len(d) else None
    print(f"   as u32x4: {u}")
    p=after; i+=1
