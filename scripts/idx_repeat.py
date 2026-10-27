import sys
path=sys.argv[1]
d=open(path,'rb').read()
body=d[16:]
# find repeated long runs: use suffix automaton-lite via dict of 8-grams
from collections import defaultdict
G=8
pos=defaultdict(list)
for i in range(len(body)-G):
    pos[body[i:i+G]].append(i)
rep=[(k,v) for k,v in pos.items() if len(v)>1]
print("distinct repeated 8-grams:", len(rep), "of", len(pos))
# longest repeated substring naive on the sample
# instead: print offsets of a distinctive gram
for gram in [b'\x75\x65\x73\x25\x5a\x2e', b'\x2e\x62\x6d\x70', b'\x2e\x64\x64\x73']:
    print(gram, [hex(i) for i in range(len(body)) if body.startswith(gram,i)][:20])
# show as rows of 63
print("=== rows of 63 bytes from body start ===")
for r in range(0, min(len(body),63*8), 63):
    print("%04x"%r, body[r:r+63].hex(' '))
