import sys,struct,collections
path=sys.argv[1]
d=open(path,'rb').read()
n1,n2=struct.unpack('<II',d[8:16])
n=len(d)
def parse(start,trailer):
    i=start;recs=[]
    while i+4<=n:
        L=struct.unpack('<I',d[i:i+4])[0]
        if not (1<=L<=250): break
        if i+4+L+trailer>n: break
        recs.append((i,L,d[i+4:i+4+L],d[i+4+L:i+4+L+trailer]))
        i=i+4+L+trailer
    return recs
best=None
for start in range(0x10,0x40):
    for tr in (8,12,16,20):
        r=parse(start,tr)
        if best is None or len(r)>len(best[2]): best=(start,tr,r)
start,tr,recs=best
print("file",path,"n1",n1,"n2",n2,"best start=0x%x trailer=%d recs=%d"%(start,tr,len(recs)))
# positional histogram of name bytes
maxL=max(L for _,L,_,_ in recs)
print("max name len",maxL)
for j in range(min(maxL,40)):
    c=collections.Counter(nm[j] for _,L,nm,_ in recs if len(nm)>j)
    top=c.most_common(3)
    tot=sum(c.values())
    print("  pos%2d n=%4d top=%s"%(j,tot,[(("%02x"%x),round(n/tot,2)) for x,n in top]))
