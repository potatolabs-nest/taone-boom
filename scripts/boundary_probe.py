import sys, os

p = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
CHUNK = 4 << 20
targets = [b'OggS', b'BM', b'DDS ', b'\x89PNG', b'\xff\xd8\xff', b'KTX 11', b'RIFF']
found = []
base = 0
tail = b''
overlap = 8
data_head = b''
buf_all = b''
with open(p, 'rb') as f:
    buf_all = f.read(64 << 20)
print(f"{os.path.basename(p)} size={os.path.getsize(p):,}")
print("head 256:", buf_all[:256].hex(' '))
for t in targets:
    i = 0
    outs = []
    while True:
        i = buf_all.find(t, i)
        if i < 0:
            break
        outs.append(i)
        i += 1
    print(f"  {t!r}: first {outs[:8]}... n={len(outs)}")
    found += outs
found = sorted(set(found))
print("first 24 candidate offsets:", found[:24])
for o in found[:n]:
    print(f"--- @{o} (0x{o:x}) ---")
    print("   pre :", buf_all[max(0,o-32):o].hex(' '))
    print("   at  :", buf_all[o:o+48].hex(' '))
    print("   asc :", repr(buf_all[max(0,o-32):o+48]))
