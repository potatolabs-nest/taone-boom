"""Use the fully-solved FxSound archive to decode .idx record semantics.

FxSound.idd = 693 back-to-back Ogg streams from offset 0.  Those exact byte
offsets must be recorded *somewhere* in FxSound.idx.  Find out how.
"""
import struct, os, sys
B = '/Users/hieu/Workspaces/taone/extracted/Boom'

# --- 1. walk the Ogg offsets in FxSound.idd (the known truth) ---
d = open(os.path.join(B, 'FxSound.idd'), 'rb').read()
n = len(d)
q = 0
offs = []
while q + 27 <= n:
    assert d[q:q + 4] == b'OggS', (q, d[q:q+4])
    nseg = d[q + 26]
    segs = d[q + 27:q + 27 + nseg]
    size = 27 + nseg + sum(segs)
    eos = d[q + 5] & 0x04
    if eos:
        offs.append((q, size))     # stream start offset, stream size
        q += size
    else:
        q += size
print(f"Ogg streams: {len(offs)}  last end = {offs[-1][0]+offs[-1][1]:,}  file = {n:,}")
print("first 5 offsets:", [o for o, s in offs[:5]])
print("first 5 sizes:  ", [s for o, s in offs[:5]])

# --- 2. look for those offsets / sizes inside FxSound.idx ---
x = open(os.path.join(B, 'FxSound.idx'), 'rb').read()
print(f"\nFxSound.idx size={len(x):,}")

targets = [o for o, s in offs]
tset = set(targets)
found = 0
for i in range(len(x) - 4):
    v = struct.unpack_from('<I', x, i)[0]
    if v in tset:
        found += 1
        if found <= 20:
            print(f"  offset {i:#06x}: value {v} == ogg offset")
print(f"  total 4-byte values matching an ogg stream start offset: {found}")

# sizes too
sizes = set(s for o, s in offs)
fs = 0
for i in range(len(x) - 4):
    v = struct.unpack_from('<I', x, i)[0]
    if v in sizes:
        fs += 1
        if fs <= 20:
            print(f"  offset {i:#06x}: value {v} == ogg STREAM SIZE")
print(f"  total matching a stream size: {fs}")

# --- 3. what about cumulative offsets in .idx? ---
# header
print("\nidx header u32s:", [struct.unpack_from('<I', x, i)[0] for i in range(0, 32, 4)])
