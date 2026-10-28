"""Scan an .idd for strictly-validated payload headers of several kinds."""
import sys, os, struct, zlib, math
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u16(b, o): return struct.unpack_from('<H', b, o)[0]


def scan(name):
    d = open(os.path.join(B, name + '.idd'), 'rb').read()
    n = len(d)
    print(f"=== {name}.idd  {n:,} bytes")

    # strict DDS
    offs = []
    i = 0
    while True:
        i = d.find(b'DDS ', i)
        if i < 0: break
        if i + 128 <= n and u32(d, i + 4) == 124 and u32(d, i + 8) & 0x1007 != 0:
            w = u32(d, i + 16); h = u32(d, i + 12)
            if 0 < w <= 8192 and 0 < h <= 8192 and w % 4 == 0 and h % 4 == 0:
                offs.append((i, w, h, d[i + 84:i + 88]))
        i += 1
    print(f"  strict DDS: {len(offs)}  first5={offs[:5]}")

    # strict BMP
    bm = []
    i = 0
    while True:
        i = d.find(b'BM', i)
        if i < 0: break
        if i + 54 <= n:
            sz = u32(d, i + 2); ob = u32(d, i + 10); dib = u32(d, i + 14)
            w, h = struct.unpack_from('<ii', d, i + 18)
            if 54 <= sz <= 40_000_000 and i + sz <= n and 14 <= ob <= sz and dib == 40 and 0 < w <= 8192 and 0 < abs(h) <= 8192:
                bm.append((i, w, h, sz))
        i += 1
    print(f"  strict BMP: {len(bm)}  first5={bm[:5]}")

    # JPEG segment chain
    jp = []
    i = 0
    while True:
        i = d.find(b'\xff\xd8\xff', i)
        if i < 0: break
        q = i + 2; ok = False
        while q + 1 < n:
            if d[q] != 0xff: break
            m = d[q + 1]; q += 2
            if m == 0xd9: break
            if m == 0xda:
                ok = True; break
            if m in (0x01,) or 0xd0 <= m <= 0xd7: continue
            if q + 2 > n: break
            ln = struct.unpack_from('>H', d, q)[0]
            if ln < 2 or q + ln > n: break
            q += ln
        if ok: jp.append(i)
        i += 1
    print(f"  JPEG chains: {len(jp)}  first5={jp[:5]}")

    # PNG
    pn = []
    i = 0
    while True:
        i = d.find(b'\x89PNG\r\n\x1a\n', i)
        if i < 0: break
        pn.append(i); i += 1
    print(f"  PNG: {len(pn)}  first5={pn[:5]}")

    return d, offs, bm, jp, pn


for nm in sys.argv[1:]:
    scan(nm)
