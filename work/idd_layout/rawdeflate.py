"""Test: are the high-entropy regions raw DEFLATE (no zlib header)?

Hypothesis: records are [u32 infl_size][raw deflate stream], i.e. the engine
used deflateInit2 with negative windowBits.  Signature: inflating at offset o
with wbits=-15 succeeds and yields exactly the u32 stored at o-4.
"""
import sys, os, struct, zlib
B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def try_raw(d, o, n):
    if o + 2 >= n:
        return None
    try:
        obj = zlib.decompressobj(-15)
        out = obj.decompress(d[o:])
        out += obj.flush()
    except Exception:
        return None
    used = (n - o) - len(obj.unused_data)
    return used, len(out)


name = sys.argv[1]
off = int(sys.argv[2], 0)
ln = int(sys.argv[3]) if len(sys.argv) > 3 else 200000
d = open(os.path.join(B, name + '.idd'), 'rb').read()
n = len(d)
end = min(n, off + ln)
print(f"{name} scan {off:#x}..{end:#x}  file={n:,}")

hits = []
o = off
while o < end - 4:
    r = try_raw(d, o, n)
    if r:
        used, outlen = r
        v = struct.unpack_from('<I', d, o - 4)[0] if o >= 4 else None
        hits.append((o, used, outlen, v, v == outlen))
        o += max(used, 1)
    else:
        o += 1
print(f"  raw-deflate successes: {len(hits)}")
for h in hits[:15]:
    print(f"   off={h[0]:#x} comp={h[1]:,} infl={h[2]:,} u32@-4={h[3]} match={h[4]}")
if hits:
    print(f"  u32@-4 == inflated: {sum(1 for h in hits if h[4])}/{len(hits)}")
    print(f"  total compressed bytes consumed: {sum(h[1] for h in hits):,}")
