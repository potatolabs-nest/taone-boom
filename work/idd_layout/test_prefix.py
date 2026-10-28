"""Test: is the u32 immediately before a zlib stream its inflated length?
If so, we have a length-prefixed record layout and can delimit payloads.
"""
import struct, os, zlib
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def streams(d):
    n = len(d)
    out = []
    i = 0
    while True:
        i = d.find(b'\x78\xda', i)
        if i < 0:
            break
        try:
            o = zlib.decompressobj(); data = o.decompress(d[i:]); data += o.flush()
            used = (n - i) - len(o.unused_data)
            out.append((i, used, len(data)))
        except Exception:
            pass
        i += 1
    return out


for name in ['FxMap', 'FxDesktop', 'FxContents', 'FxStage', 'FxCharacter']:
    d = open(os.path.join(B, name + '.idd'), 'rb').read()
    ss = streams(d)
    ok = 0
    near = 0
    detail = []
    for (i, used, outlen) in ss:
        if i < 4:
            continue
        v = struct.unpack_from('<I', d, i - 4)[0]
        if v == outlen:
            ok += 1
        elif abs(v - outlen) < 64:
            near += 1
            detail.append((i, used, outlen, v))
    print(f"{name}: {len(ss)} streams, u32@(i-4)==inflated: {ok}  near(<64): {near}")
    for t in detail[:6]:
        print("    ", t)
