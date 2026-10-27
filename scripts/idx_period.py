import sys, collections
path = sys.argv[1]
data = open(path,'rb').read()
body = data[16:]
n = len(body)
print("file", path, "len", len(data), "body", n)
# XOR autocorrelation: fraction of zero bytes for shift P
best=[]
for P in range(1, 512):
    z = sum(1 for i in range(n-P) if body[i]==body[i+P])
    best.append((z/(n-P), P))
best.sort(reverse=True)
print("TOP XOR-equal fraction (P, frac):")
for f,P in best[:15]:
    print("  P=%4d frac=%.4f" % (P,f))
# subtract
best=[]
for P in range(1,512):
    z = sum(1 for i in range(n-P) if ((body[i]-body[i+P])&0xff)==0)
    best.append((z/(n-P), P))
best.sort(reverse=True)
print("TOP SUB-equal (trivial, same as XOR=):")
for f,P in best[:5]:
    print("  P=%4d frac=%.4f" % (P,f))
