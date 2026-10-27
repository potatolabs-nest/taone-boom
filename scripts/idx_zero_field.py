import sys,struct,collections
def parse_start(path,start=0x37,L0=None,rec0_extra=0):
    d=open(path,'rb').read(); n=len(d)
    # record: [u32 L][name L][16 tail]  ; next record immediately after tail
    i=start; recs=[]
    while i+20<=n:
        L=struct.unpack('<I',d[i:i+4])[0]
        if not(1<=L<=250): break
        if i+4+L+16>n: break
        name=d[i+4:i+4+L]; tail=d[i+4+L:i+4+L+16]
        recs.append((i,L,name,tail))
        i=i+4+L+16
    return d,recs
path=sys.argv[1]
d,recs=parse_start(path)
print(path.split('/')[-1],"recs",len(recs))
# group tails by L, look at the LAST 4 bytes (assumed plaintext zero) and first 4 (ext)
byL=collections.defaultdict(list)
for i,L,name,tail in recs: byL[L].append(tail)
print("L : count : distinct_last4_zero : distinct_first4_ext")
for L in sorted(byL)[:20]:
    tails=byL[L]
    last4=collections.Counter(t[12:16] for t in tails)
    first4=collections.Counter(t[0:4] for t in tails)
    print("%3d : %4d : last4 distinct=%d %s : first4 distinct=%d %s" % (
        L,len(tails),len(last4),[ (k.hex(),v) for k,v in last4.most_common(2)],
        len(first4),[(k.hex(),v) for k,v in first4.most_common(2)]))
