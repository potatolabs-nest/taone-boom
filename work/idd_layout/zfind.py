import struct, sys, os, zlib
B='/Users/hieu/Workspaces/taone/extracted/Boom'
name=sys.argv[1]
d=open(os.path.join(B,name+'.idd'),'rb').read()
n=len(d)
# all zlib stream starts
hits=[]
i=0
while True:
    i=d.find(b'\x78\xda', i)
    if i<0: break
    try:
        o=zlib.decompressobj(); out=o.decompress(d[i:]); out+=o.flush()
        used=(n-i)-len(o.unused_data)
        if len(out)>=1: hits.append((i,used,len(out)))
    except Exception: pass
    i+=1
print(f"{name}: {len(hits)} zlib streams")
if hits:
    print("  first 10:", hits[:10])
    print("  offsets min/max:", hits[0][0], hits[-1][0])
    gaps=[hits[k+1][0]-hits[k][0] for k in range(len(hits)-1)]
    from collections import Counter
    print("  gap common:", Counter(gaps).most_common(8))
