import sys, zlib, os, collections
MAG={b'DDS ':'dds',b'BM':'bmp',b'\xff\xd8\xff':'jpg',b'\x89PNG':'png',b'OggS':'ogg',b'RIFF':'riff',b'BZh':'bz2',b'KTX':'ktx'}
def classify(out):
    for m,n in MAG.items():
        if out[:len(m)]==m: return n
    # nested/other
    for m,n in MAG.items():
        if out.find(m)>0: return 'contains:'+n
    return 'struct'
p=sys.argv[1]; d=open(p,'rb').read()
found=[]; i=0
while True:
    i=d.find(b'\x78\xda',i)
    if i<0: break
    try:
        o=zlib.decompressobj(); out=o.decompress(d[i:])+o.flush()
        if len(out)>32:
            # consumed bytes = len(d[i:]) - len(o.unused_data)
            used=len(d[i:])-len(o.unused_data)
            found.append((i,used,len(out),classify(out)))
    except Exception: pass
    i+=1
print(f"=== {os.path.basename(p)} ({len(d):,})  valid zlib streams: {len(found)}")
print("  output classes:", collections.Counter(c for _,_,_,c in found).most_common())
cov=sum(u for _,u,_,_ in found)
print(f"  compressed bytes consumed: {cov:,}  ({100*cov/len(d):.1f}% of idd)")
print(f"  inflated total: {sum(o for _,_,o,_ in found):,}")
for f in found[:6]:
    print(f"   @{f[0]:>10,} used={f[1]:>9,} out={f[2]:>9,} {f[3]}")
