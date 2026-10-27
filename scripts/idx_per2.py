import sys
d=open(sys.argv[1],'rb').read(); body=d[16:]
n=len(body)
# For each position, find longest match at distance 63
P=63
runs=[]
i=0
while i<n-P:
    l=0
    while i+l<n-P and body[i+l]==body[i+l+P]:
        l+=1
    if l>=4: runs.append((i,l))
    i+=max(1,l)
print("matches at lag 63 with len>=4:")
for i,l in runs[:30]: print("  @%05x len=%d : %s"%(i,l,body[i:i+l].hex(' ')))
print("total runs", len(runs), "maxlen", max(l for _,l in runs))
