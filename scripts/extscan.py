import sys, os, struct
EXTS=[b'.bmp',b'.dds',b'.ogg',b'.png',b'.jpg',b'.tga',b'.ani',b'.scr',b'.txt',b'.xml',b'.msk',b'.wav',b'.dat',b'.cur',b'.ico',b'.pak',b'.ttf',b'.dib']
for path in sys.argv[1:]:
    d=open(path,'rb').read()
    print(f"=== {os.path.basename(path)} ({len(d)}) ===")
    hits=[]
    for e in EXTS:
        i=0
        while True:
            i=d.find(e,i)
            if i<0: break
            hits.append((i,e)); i+=1
    hits.sort()
    print(f"  {len(hits)} extension markers")
    for o,e in hits[:40]:
        # show surrounding context
        print(f"   @{o:<6} 0x{o:04x} {e.decode():5s}  ctx: {d[max(0,o-8):o+6].hex(' ')}")
    if hits:
        deltas=[hits[i+1][0]-hits[i][0] for i in range(len(hits)-1)]
        from collections import Counter
        print("  deltas:", Counter(deltas).most_common(10))
