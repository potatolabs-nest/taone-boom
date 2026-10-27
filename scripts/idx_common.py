import sys,struct,collections
path=sys.argv[1]; d=open(path,'rb').read(); n=len(d)
def parse(start,tr):
    i=start;out=[]
    while i+4<=n:
        L=struct.unpack('<I',d[i:i+4])[0]
        if not(1<=L<=250): break
        if i+4+L+tr>n: break
        out.append((i,L,d[i+4:i+4+L],d[i+4+L:i+4+L+tr])); i=i+4+L+tr
    return out
best=max(((s,t,parse(s,t)) for s in range(0x10,0x40) for t in (8,12,16,20)),key=lambda x:len(x[2]))
start,tr,recs=best
print("start=0x%x tr=%d recs=%d"%(start,tr,len(recs)))
c=collections.Counter((L,nm,tail) for _,L,nm,tail in recs)
print("distinct (L,name,trailer) triples:",len(c))
for (L,nm,tail),cnt in c.most_common(12):
    print("cnt=%-4d L=%-3d name(%d)=%s tail=%s"%(cnt,L,len(nm),nm.hex(' '),tail.hex(' ')))
# also distinct names alone
cn=collections.Counter(nm for _,L,nm,_ in recs)
print("distinct names:",len(cn),"of",len(recs))
for nm,cnt in cn.most_common(8):
    print("  namecnt=%d %s  |%s|"%(cnt,nm.hex(' '),''.join(chr(b) if 32<=b<127 else '.' for b in nm)))
