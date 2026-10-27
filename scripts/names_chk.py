import struct,re,os,collections
d=open('/Users/hieu/Workspaces/taone/work/ssi/product.ini.bin','rb').read()
print("product.ini size",len(d))
for off in range(0,0x60,16):
    c=d[off:off+16]; print('%05x'%off,c.hex(' '),''.join(chr(x) if 32<=x<127 else '.' for x in c))
print("--- tail ---")
for off in range(len(d)-0x40,len(d),16):
    c=d[off:off+16]; print('%05x'%off,c.hex(' '),''.join(chr(x) if 32<=x<127 else '.' for x in c))
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom"
for ext in ("dds","DDS","tga","ani","scr","eff","tmb"):
    n=0
    for root,_,fs in os.walk(BOOM):
        for f in fs:
            p=os.path.join(root,f)
            try: dd=open(p,'rb').read()
            except: continue
            n+=len(re.findall((r'\.'+ext+r'\b').encode(), dd, re.I))
    print("ext .%s total hits %d"%(ext,n))
# DDS magic ' DDS ' / 'DDS ' in idds
for root,_,fs in os.walk(BOOM):
    for f in fs:
        if f.endswith(".idd"):
            dd=open(os.path.join(root,f),'rb').read()
            c=dd.count(b'DDS ')
            if c: print("  DDS magic in",os.path.relpath(os.path.join(root,f),BOOM),c)
