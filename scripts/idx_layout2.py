import sys,struct,collections
def parse(path):
    d=open(path,'rb').read(); n=len(d)
    # layout: [name(L)] [ext4][size u32][size u32][zero u32] [u32 nextL]
    # find first record: header 16 bytes, record0 name starts at 0x10, len unknown.
    # We know nextL sits right after each 16-byte tail. Walk backwards is hard; instead:
    # names have a u32 nextL after tail. Try: record0 len = ?
    return d
def walk(path):
    d=open(path,'rb').read(); n=len(d)
    # find the first 'nextL' by scanning for u32 in [1,250] followed by plausible name
    # Simpler: try every start for record0 length so that chain reaches EOF exactly
    for L0 in range(1,120):
        i=0x10; ok=True; recs=[]
        L=L0
        while True:
            if i+L+16+4>n: break
            nm=d[i:i+L]; t=d[i+L:i+L+16]
            nxt=struct.unpack('<I',d[i+L+16:i+L+20])[0]
            recs.append((i,L,nm,t))
            i=i+L+20
            if i>=n: break
            L=nxt
            if not(1<=L<=250): ok=False; break
        if ok and i==n and len(recs)>=2:
            return L0,recs
    return None,[]
for path in sys.argv[1:]:
    L0,recs=walk(path)
    d=open(path,'rb').read()
    if not recs: print(path,"NO WALK"); continue
    exts=collections.Counter(r[3][:4] for r in recs)
    sizes=[struct.unpack('<I',r[3][4:8])[0] for r in recs]
    sizes2=[struct.unpack('<I',r[3][8:12])[0] for r in recs]
    zeros=sum(1 for r in recs if r[3][12:16]==b'\x00\x00\x00\x00')
    eq=sum(1 for a,b in zip(sizes,sizes2) if a==b)
    print("%-24s recs=%d L0=%d iddlen=%d sum(size)=%d sum(size2)=%d" % (
        path.split('/')[-1],len(recs),L0,len(d),sum(sizes),sum(sizes2)))
    print("   ext dist:", {k.decode('latin1'):v for k,v in exts.most_common(8)})
    print("   tail[12:16]==0: %d/%d   size==size2: %d/%d" % (zeros,len(recs),eq,len(recs)))
