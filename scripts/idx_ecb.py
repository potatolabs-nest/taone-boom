import sys,collections
for path in sys.argv[1:]:
    d=open(path,'rb').read()[16:]
    # ECB test: repeated 16-byte blocks aligned to 16
    blocks=[d[i:i+16] for i in range(0,len(d)-15,16)]
    c=collections.Counter(blocks)
    rep=[(b,n) for b,n in c.most_common(3) if n>1]
    print(path.split('/')[-1], "n16blocks",len(blocks),"repeats",len(rep), rep[:2])
    # repeated blocks at ANY alignment
    c2=collections.Counter(d[i:i+8] for i in range(len(d)-7))
    top=[(b,n) for b,n in c2.most_common(5) if n>1]
    print("    top8:", [(x.hex(),n) for x,n in top])
