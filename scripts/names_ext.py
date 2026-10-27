import os, re, collections, struct
ROOT="/Users/hieu/Workspaces/taone"
SSI=os.path.join(ROOT,"work/ssi")
BOOM=os.path.join(ROOT,"extracted/Boom")
KNOWN=set("bmp dds tga png jpg jpeg ogg ani scr msk eff bik avi wav mp3 tmb dat ini ssd idx idd pak fft ttf exe dll dat aes cfg log sys asi dll".split())
hits=collections.Counter(); ctx=collections.defaultdict(collections.Counter)
# 1) every text-ish file in work/ssi (.bin + .strings.txt)
for fn in sorted(os.listdir(SSI)):
    d=open(os.path.join(SSI,fn),'rb').read()
    for m in re.finditer(rb'[A-Za-z0-9_\-/\\]{1,80}\.([A-Za-z][A-Za-z0-9]{1,4})(?![A-Za-z0-9])', d):
        e=m.group(1).decode().lower()
        hits[e]+=1; ctx[e][m.group(0).decode('latin-1')]+=1
# 2) magic bytes in .idd
MAGICS={b'OggS':'ogg',b'BM':'bmp',b'DDS ':'dds',b'RIFF':'riff',b'\x89PNG':'png',b'\xff\xd8\xff':'jpg',b'BKHD':'bik',b'\x89KTX':'ktx'}
mag=collections.Counter()
for fn in sorted(os.listdir(BOOM)):
    if not fn.endswith('.idd'): continue
    d=open(os.path.join(BOOM,fn),'rb').read(1<<20)
    for sig,name in MAGICS.items():
        c=d.count(sig)
        if c: mag[name]+=c
print("=== extension-like tokens in decoded data (top 40) ===")
for e,c in hits.most_common(40):
    print("  %-6s %-6d  e.g. %s"%(e,c,list(ctx[e])[:3]))
print()
print("=== magic counts in first 1MB of each .idd ===")
print(dict(mag))
