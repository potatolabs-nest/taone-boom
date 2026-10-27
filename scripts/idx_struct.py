import sys,struct
path=sys.argv[1]
d=open(path,'rb').read()
print("file",path,"len",len(d))
print("hdr magic",d[:4].hex(),"ver",struct.unpack('<I',d[4:8])[0],
      "n1",struct.unpack('<I',d[8:12])[0],"n2",struct.unpack('<I',d[12:16])[0])
# scan for u32 in [1,255] positions in body
cands=[]
for i in range(16, len(d)-4):
    v=struct.unpack('<I',d[i:i+4])[0]
    if 1<=v<=255:
        cands.append((i,v))
# greedily walk: start at 0x10
print("--- try walk from 0x10 ---")
i=0x10
rec=0
while i+4 < len(d) and rec<12:
    # name assumed at i; find namelen field: assume name length is encoded somewhere
    # print 48 bytes
    print("off %04x: %s"%(i, d[i:i+48].hex(' ')))
    i+=63; rec+=1
