import sys, zlib, struct, os

def decompress(path):
    d = open(path,'rb').read()
    magic = d[:4]
    i = d.find(b'\x78\xda')
    if i < 0: i = d.find(b'\x78\x9c')
    if i < 0: return magic, b''
    o = zlib.decompressobj()
    out = o.decompress(d[i:]) + o.flush()
    return magic, out

def parse_table(out):
    """Try: 6-byte header then repeated [u32 len][bytes]."""
    for hdr in (6, 4, 0):
        try:
            p = hdr; items = []
            while p + 4 <= len(out):
                n = struct.unpack_from('<I', out, p)[0]
                if n == 0 or n > len(out) - p - 4: raise ValueError
                items.append(out[p+4:p+4+n]); p += 4 + n
            if p == len(out) and len(items) > 10:
                return hdr, items
        except Exception:
            pass
    return None, []

if __name__ == '__main__':
    for path in sys.argv[1:]:
        magic, out = decompress(path)
        hdr, items = parse_table(out)
        print(f"=== {path}  magic={magic}  raw={os.path.getsize(path)}  inflate={len(out)}  hdr={hdr}  items={len(items)}")
        for it in items[:12]:
            print("   ", it[:90])
