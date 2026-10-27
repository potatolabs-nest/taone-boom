import sys, zlib, io
p = sys.argv[1]
d = open(p,'rb').read()
print("size", len(d), "magic", d[:4])
i = d.find(b'\x78\xda')
print("zlib at", i)
for start in ([i] if i>=0 else []):
    for hdr in range(4, 40):
        off = start
        try:
            o = zlib.decompressobj()
            out = o.decompress(d[off:])
            out += o.flush()
            print("OK off",off,"outlen",len(out))
            print(repr(out[:600]))
            sys.exit(0)
        except Exception as e:
            pass
print("no luck")
