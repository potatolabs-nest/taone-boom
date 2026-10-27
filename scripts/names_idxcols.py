import struct,sys,os,collections,math
def vis(b): return ''.join(chr(c) if 32<=c<127 else '.' for c in b)
def records(d, start=0x0c):
    """chain [u32 L][L bytes][u32 a][u32 b][u32 c]"""
    i=start; out=[]
    n=len(d)
    while i+16<=n:
        L=struct.unpack_from('<I',d,i)[0]
        if not (1<=L<=128): break
        if i+4+L+12>n: break
        nm=d[i+4:i+4+L]
        a,b,c=struct.unpack_from('<III',d,i+4+L)
        out.append((i,L,nm,a,b,c)); i=i+4+L+12
    return out
for p in sys.argv[1:]:
    d=open(p,'rb').read()
    rs=records(d)
    print("=== %s size=%d recs=%d (chained)"%(os.path.basename(p),len(d),len(rs)))
    for (o,L,nm,a,b,c) in rs[:10]:
        print("   @0x%05x L=%-3d %-30s |%s| a=%d b=%d c=%d"%(o,L,nm.hex(' '),vis(nm),a,b,c))
    if len(rs)>=20:
        # column constancy
        W=min(L for _,L,_,_,_,_ in rs)
        ent=[]
        for j in range(min(W,40)):
            col=[nm[j] for _,L,nm,_,_,_ in rs if L>j]
            cnt=collections.Counter(col)
            H=-sum(v/len(col)*math.log2(v/len(col)) for v in cnt.values())
            ent.append(H)
            top=cnt.most_common(2)
        print("   len(min)=%d  column entropy:"%W)
        print("   ", " ".join("%.2f"%e for e in ent))
        for j in range(min(W,24)):
            col=[nm[j] for _,L,nm,_,_,_ in rs if L>j]
            cnt=collections.Counter(col); mc,cv=cnt.most_common(1)[0]
            print("      col%-2d const=%.0f%% val=%02x %r"%(j,100*cv/len(col),mc,chr(mc) if 32<=mc<127 else '.'))
