import sys, os, zlib, struct
ROOT='/Users/hieu/Workspaces/taone'
BOOM=os.path.join(ROOT,'extracted/Boom')

def scan(name):
    p=os.path.join(BOOM,'ndadata',name+'.idd')
    d=open(p,'rb').read()
    print(f'== {name} idd={len(d)}')
    hits=[]
    for i in range(len(d)-2):
        if d[i]==0x78 and d[i+1] in (0x01,0x5e,0x9c,0xda):
            try:
                z=zlib.decompressobj()
                out=z.decompress(d[i:i+8_000_000])
                if len(out)>64:
                    hits.append((i,len(out),len(d[i:i+8_000_000])-len(z.unused_data),out[:4]))
            except Exception:
                pass
    for i,olen,clen,magic in hits:
        print(f'  zlib@{i} -> {olen} bytes (consumed {clen}) magic={magic!r}')
    print(f'  {len(hits)} streams')
if __name__=='__main__':
    for n in sys.argv[1:]: scan(n)
