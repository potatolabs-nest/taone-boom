import struct,sys,os,collections
def anchors(d):
    out=[]
    for p in range(0,len(d)-12):
        a=struct.unpack_from('<I',d,p)[0]
        b=struct.unpack_from('<I',d,p+4)[0]
        c=struct.unpack_from('<I',d,p+8)[0]
        if a==b and c==0 and 0<a<50_000_000:
            out.append((p,a))
    return out
def vis(b): return ''.join(chr(c) if 32<=c<127 else '.' for c in b)
for f in sys.argv[1:]:
    d=open(f,'rb').read()
    an=anchors(d)
    print("=== %s (%d bytes) anchors=%d"%(os.path.basename(f),len(d),len(an)))
    prev=None
    for p,a in an[:12]:
        gap = "" if prev is None else " gap=%d"%(p-prev)
        print("   anchor@0x%05x val=%-9d%s   prevbytes=%s"%(p,a,gap,vis(d[max(0,p-12):p])))
        prev=p
    # if anchors are contiguous with fixed stride, show stride histogram
    if len(an)>2:
        strides=collections.Counter(an[i+1][0]-an[i][0] for i in range(len(an)-1))
        print("   stride hist:",strides.most_common(6))
