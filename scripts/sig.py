import sys, struct, os, zlib
from collections import Counter
p=sys.argv[1]; d=open(p,'rb').read()
if d[:4]==b'PACK':
    zf=d.find(b'\x78\xda'); o=zlib.decompressobj(); d=o.decompress(d[zf:])+o.flush()
print(f"{os.path.basename(p)} len={len(d)}")
# find [v,v,0] u32 triples
sig=[]
for q in range(0, len(d)-12):
    a,b,c=struct.unpack_from('<3I', d, q)
    if a==b and 0<a<10_000_000 and c==0: sig.append(q)
print("triple(v,v,0) positions:", [hex(s) for s in sig])
print("deltas:", [sig[i+1]-sig[i] for i in range(len(sig)-1)])
# annotate: for each triple, look back for a plausible u32 length and 24-ish name
for s in sig:
    for back in range(4, 40):
        q=s-back
        if q<0: continue
        L=struct.unpack_from('<I', d, q)[0]
        if 0<L<200 and q+4+L==s:
            nm=d[q+4:s]
            print(f"  triple@{s} -> L@{q} = {L} (gap {back})  name={nm!r}")
