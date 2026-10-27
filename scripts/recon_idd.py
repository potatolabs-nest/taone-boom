import sys, os, struct, collections

CHUNK = 8 << 20
MAGICS = {
    b'OggS': 'ogg',
    b'DDS ': 'dds',
    b'RIFF': 'riff',
    b'BM\xc0': 'bmp?',   # placeholder, real BM check below
    b'\x89PNG\r\n\x1a\n': 'png',
    b'\xff\xd8\xff': 'jpg',
    b'KTX 11': 'ktx',
    b'\x1f\x8b\x08': 'gzip',
    b'ID3': 'mp3',
    b'BZh9': 'bz2',
    b'\x78\xda': 'zlib',
    b'CWS': 'swf',
    b'FWS': 'swf',
    b'PACK0001': 'pack',
    b'ssi1': 'ssi1',
    b'ssi3': 'ssi3',
    b'GIF8': 'gif',
    b'ftyp': 'mp4',
}
# BM magic must be followed by a plausible bfSize
def scan(path):
    size = os.path.getsize(path)
    counter = collections.Counter()
    gaps = collections.Counter()
    positions = collections.defaultdict(list)
    key = b'BM'
    prev = None
    overlap = 16
    tail = b''
    base = 0
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            buf = tail + chunk
            off = base - len(tail)
            allmagics = dict(MAGICS)
            allmagics[b'BM'] = 'bm'
            for m, name in allmagics.items():
                i = 0
                while True:
                    i = buf.find(m, i)
                    if i < 0:
                        break
                    gpos = off + i
                    if name == 'bm':
                        if i + 6 <= len(buf) or (off + i + 6 <= size):
                            # need bfSize
                            pass
                    counter[name] += 1
                    positions[name].append(gpos)
                    i += 1
            base += len(chunk)
            tail = buf[-overlap:]
    return size, counter, positions

for p in sys.argv[1:]:
    size, counter, positions = scan(p)
    name = os.path.basename(p)
    print(f"=== {name} size={size:,} frames={sum(counter.values()):,}")
    for k, v in counter.most_common():
        print(f"    {k:10s} {v:>9,}")
    # alignment of ogg
    for k in ('ogg', 'dds', 'bm', 'riff', 'png', 'jpg'):
        ps = positions.get(k)
        if not ps:
            continue
        mods = collections.Counter(x % 8 for x in ps)
        print(f"    align {k}: mod8={dict(sorted(mods.items()))}")
