import struct, os, zlib
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


d = open(os.path.join(B, 'FxMap.idd'), 'rb').read()
n = len(d)
ss = streams(d)
head = d[:940000]

# candidate tables of the values we know
targets = {}
for k, (i, used, outlen) in enumerate(ss[:5]):
    targets[i] = f"zliboff{k}"
    targets[used] = f"compsz{k}"
    targets[outlen] = f"inflsz{k}"
print("looking in first 940 KB for known stream values:")
for v, lab in targets.items():
    hits = []
    start = 0
    while True:
        p = head.find(struct.pack('<I', v), start)
        if p < 0: break
        hits.append(p); start = p + 1
    print(f"  {lab}: {v:,} -> {len(hits)} hits {hits[:6]}")

# Same for all stream offsets: count how many appear in the head
offs = set(i for i, u, o in ss)
cnt = 0
for p in range(0, len(head) - 4, 4):
    if struct.unpack_from('<I', head, p)[0] in offs:
        cnt += 1
print(f"\n4-byte-aligned head values equal to a zlib stream offset: {cnt}")
