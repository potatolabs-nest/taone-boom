import sys,struct
path=sys.argv[1]; start=int(sys.argv[2],16) if len(sys.argv)>2 else 0x37
d=open(path,'rb').read(); n=len(d)
n1,n2=struct.unpack('<II',d[8:16])
print("file",path,"len",n,"n1",n1,"n2",n2,"start",hex(start))
i=start; k=0
while i+4<=n and k<8:
    L=struct.unpack('<I',d[i:i+4])[0]
    if not (4<=L<=250): print("  STOP at 0x%x L=%d"%(i,L)); break
    name=d[i+4:i+4+L]
    t=i+4+L
    tail=d[t:t+16]
    dw=[struct.unpack('<I',tail[j:j+4])[0] for j in (0,4,8,12)]
    print("rec%-3d @%05x L=%-3d tail@%05x dw=%s name=%s" % (k,i,L,t,dw,name.decode('latin1').encode('unicode_escape').decode()))
    i=t+16; k+=1
print("first record area 0x10..0x36:", d[0x10:0x37].hex(' '))
