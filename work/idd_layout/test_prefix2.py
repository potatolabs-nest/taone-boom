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


for name in ['FxMap', 'FxDesktop', 'FxHiddenCatch', 'FxContents', 'FxStage', 'FxCharacter', 'fx', 'FxMonster']:
    d = open(os.path.join(B, name + '.idd'), 'rb').read()
    ss = streams(d)
    if not ss:
        print(f"{name}: 0 streams"); continue
    a = b = 0
    for (i, used, outlen) in ss:
        if i >= 8 and struct.unpack_from('<I', d, i - 8)[0] == used: a += 1
        if i >= 4 and struct.unpack_from('<I', d, i - 4)[0] == outlen: b += 1
    print(f"{name}: {len(ss)} streams | [i-8]==comp: {a}  [i-4]==infl: {b}")
