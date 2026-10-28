import struct, os, zlib
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def streams(d):
    n = len(d); out = []; i = 0
    while True:
        i = d.find(b'\x78\xda', i)
        if i < 0: break
        try:
            o = zlib.decompressobj(); data = o.decompress(d[i:]); data += o.flush()
            used = (n - i) - len(o.unused_data)
            out.append((i, used, len(data)))
        except Exception: pass
        i += 1
    return out


for name in ['FxMap', 'FxDesktop', 'FxHiddenCatch']:
    d = open(os.path.join(B, name + '.idd'), 'rb').read()
    n = len(d)
    ss = streams(d)
    print(f"\n=== {name}.idd {n:,}  streams={len(ss)}")
    if not ss:
        continue
    # contiguity check
    contiguous = 0
    gaps = []
    for k in range(len(ss) - 1):
        end = ss[k][0] + ss[k][1]
        if end == ss[k + 1][0] - 8:
            contiguous += 1
        else:
            gaps.append((ss[k][0], end, ss[k + 1][0] - 8, ss[k + 1][0] - 8 - end))
    print(f"  contiguous pairs: {contiguous}/{len(ss)-1}; breaks: {len(gaps)}")
    for g in gaps[:10]:
        print(f"    break after stream@{g[0]:#x}: end={g[1]:#x} next_hdr={g[2]:#x} gap={g[3]:,}")
    # total contiguous run coverage
    if contiguous == len(ss) - 1:
        first = ss[0][0] - 8
        last = ss[-1][0] + ss[-1][1]
        print(f"  ALL contiguous: run from {first:#x} to {last:#x} = {last-first:,} bytes "
              f"({(last-first)/n*100:.2f}% of file)")
        print(f"  head before run: {first:,} bytes; tail after run: {n-last:,} bytes")
