import struct, os, zlib
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
name = 'FxMap'
d = open(os.path.join(B, name + '.idd'), 'rb').read()
n = len(d)


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


ss = streams(d)
print(f"{name}: {len(ss)} streams")
prev_end = None
for k in range(10):
    i, used, outlen = ss[k]
    start = i - 8
    print(f"\n--- stream {k} at {i:#x} comp={used} infl={outlen}")
    print(f"  record (guess) starts at {start:#x}; bytes before that:")
    lo = max(0, start - 48)
    for a in range(lo, start, 16):
        row = d[a:a + 16]
        print(f"    {a:>9} 0x{a:08x} " + ' '.join(f'{b:02x}' for b in row) + '  ' + ''.join(chr(b) if 32 <= b < 127 else '.' for b in row))
    if prev_end is not None:
        print(f"  prev record zlib end={prev_end:#x}  gap to this rec header = {start - prev_end}")
    prev_end = i + used
