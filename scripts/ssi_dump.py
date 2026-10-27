import sys, zlib
d=open(sys.argv[1],'rb').read()
i=d.find(b'\x78\xda')
o=zlib.decompressobj(); out=o.decompress(d[i:])+o.flush()
n=int(sys.argv[2]) if len(sys.argv)>2 else 300
print("inflated len", len(out))
print(repr(out[:n]))
