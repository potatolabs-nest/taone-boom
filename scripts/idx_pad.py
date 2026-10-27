import sys,collections,math
# character scoring: printable ASCII + common filename chars score high
def score(b):
    c=chr(b)
    if c.isalnum(): return 3.0
    if c in './_-\\': return 2.5
    if c in '~!@#$%^&*()+=[]{};:,<>?|': return 1.0
    if c==' ': return 0.5
    return -6.0   # control/high bytes penalised

def attack(body, L, op='xor'):
    key=[]
    for r in range(L):
        cnt=collections.Counter(body[i] for i in range(r,len(body),L))
        best=None
        for k in range(256):
            if op=='xor':
                s=sum(n*score(b^k) for b,n in cnt.items())
            else:
                s=sum(n*score((b-k)&0xff) for b,n in cnt.items())
            if best is None or s>best[0]: best=(s,k)
        key.append(best[1])
    # score of recovered plaintext
    pt=bytearray(len(body))
    for i,b in enumerate(body):
        k=key[i%L]
        pt[i]= (b^k) if op=='xor' else ((b-k)&0xff)
    good=sum(1 for b in pt if score(b)>=1.0)
    return good/len(body), key, bytes(pt)

path=sys.argv[1]
d=open(path,'rb').read()
body=d[16:]
print("file",path,"body",len(body))
best=[]
for op in ('xor','sub'):
    for L in list(range(1,65))+[80,96,112,128,160,192,256]:
        fr,key,pt=attack(body,L,op)
        best.append((fr,op,L,key,pt))
best.sort(key=lambda x:-x[0])
for fr,op,L,key,pt in best[:6]:
    print("op=%s L=%3d printable=%.3f key=%s"%(op,L,fr,bytes(key).hex()))
    print("   pt[:80]:",pt[:80])
