import sys, struct, os, zlib, glob
def load(p):
    d=open(p,'rb').read()
    if d[:4]==b'PACK':
        zf=d.find(b'\x78\xda'); o=zlib.decompressobj(); return o.decompress(d[zf:])+o.flush()
    return d

def try_layout(d, idd_size):
    """Hypothesis: rec0 = [name][A][B][C]; rec_i = [u32 len][name][X][A][B][C]"""
    out=[]
    p=16
    # rec0: find first position where [A][B][C=0] fits and next u32 is plausible len
    return None

for p in sys.argv[1:]:
    d=load(p)
    base=os.path.splitext(p)[0]
    n=os.path.getsize(base+'.idd') if os.path.exists(base+'.idd') else 0
    print("="*100)
    print(f"{os.path.basename(p)} size={len(d)} idd={n:,}  hdr={struct.unpack_from('<4I',d,0)}")
    # dump full hex in rows of the probable structure
    for off in range(0, len(d), 16):
        row=d[off:off+16]
        print(f"  {off:04x}: {row.hex(' '):<48} |{''.join(chr(b) if 32<=b<127 else '.' for b in row)}|")
