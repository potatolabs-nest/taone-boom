import sys, struct, os, zlib
from collections import Counter

def load(p):
    d = open(p, 'rb').read()
    if d[:4] == b'PACK':
        zf = d.find(b'\x78\xda')
        o = zlib.decompressobj()
        return o.decompress(d[zf:]) + o.flush()
    return d

def dump(p, maxrows=None):
    d = load(p)
    print("=" * 100)
    print(f"{os.path.basename(p)} size={len(d)} hdr={struct.unpack_from('<4I', d, 0)}")
    for off in range(0, len(d), 16):
        if maxrows and off // 16 >= maxrows:
            break
        row = d[off:off + 16]
        print(f"  {off:04x}: {row.hex(' '):<48} |{''.join(chr(b) if 32 <= b < 127 else '.' for b in row)}|")

def zeropos(d):
    zs = [q for q in range(16, len(d) - 3) if struct.unpack_from('<I', d, q)[0] == 0]
    # collapse overlapping runs
    out = []
    for q in zs:
        if out and q - out[-1][-1] <= 1:
            out[-1].append(q)
        else:
            out.append([q])
    return [(g[0], g[-1]) for g in out]

def prefix_groups(d, n=16):
    """find all positions where the n-byte string starting there also occurs elsewhere"""
    groups = {}
    for q in range(16, len(d) - n):
        key = d[q:q + n]
        groups.setdefault(key, []).append(q)
    gs = [(k, v) for k, v in groups.items() if len(v) > 1]
    gs.sort(key=lambda kv: -len(kv[1]))
    return gs

def main():
    for p in sys.argv[1:]:
        d = load(p)
        dump(p)
        zs = zeropos(d)
        print("zero-u32 runs:", [(hex(a), hex(b)) for a, b in zs][:40])
        print("run-start deltas:", [zs[i + 1][0] - zs[i][0] for i in range(len(zs) - 1)][:40])
        gs = prefix_groups(d, 12)
        print(f"repeated 12-byte prefixes: {len(gs)}")
        for k, v in gs[:6]:
            print(f"   {k.hex(' ')} n={len(v)} at {[hex(x) for x in v[:12]]}")
            if len(v) > 2:
                print(f"      deltas={[v[i+1]-v[i] for i in range(len(v)-1)][:15]}")
        print()

main()
