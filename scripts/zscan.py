import sys, zlib, os
p=sys.argv[1]; d=open(p,'rb').read()
print(f"=== {os.path.basename(p)} ({len(d):,})")
for hdr in (b'\x78\xda', b'\x78\x9c', b'\x78\x01'):
    hits=[]; i=0
    while True:
        i=d.find(hdr,i)
        if i<0: break
        hits.append(i); i+=1
        if len(hits)>200000: break
    print(f"  {hdr.hex()}: {len(hits):,} occurrences")
# try inflating the first N zlib candidates
ok=0; fail=0; sizes=[]
i=0; tried=0
while tried<400:
    i=d.find(b'\x78\xda', i)
    if i<0: break
    tried+=1
    try:
        o=zlib.decompressobj(); out=o.decompress(d[i:])+o.flush()
        if len(out)>64:
            ok+=1; sizes.append(len(out))
            if ok<=3: print(f"    @{i:,} -> {len(out):,} bytes  head={out[:16]!r}")
    except Exception:
        fail+=1
    i+=1
print(f"  inflate test: {ok} succeeded, {fail} failed (of {tried} candidates)")
if sizes: print(f"  inflated sizes: min={min(sizes):,} max={max(sizes):,}")
