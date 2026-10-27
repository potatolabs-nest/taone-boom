import sys, zlib, os, glob, re, json
outdir = sys.argv[1]
os.makedirs(outdir, exist_ok=True)
files = sorted(glob.glob('/Users/hieu/Workspaces/taone/extracted/Boom/*.ssd') +
               glob.glob('/Users/hieu/Workspaces/taone/extracted/Boom/*.ini') +
               glob.glob('/Users/hieu/Workspaces/taone/extracted/Boom/*.cfg') +
               glob.glob('/Users/hieu/Workspaces/taone/extracted/Boom/*.dat') +
               glob.glob('/Users/hieu/Workspaces/taone/extracted/Boom/ndadata/*.ssd') +
               glob.glob('/Users/hieu/Workspaces/taone/extracted/Boom/ndadata/*.ini'))
summary = []
for f in files:
    d = open(f,'rb').read()
    magic = d[:4]
    i = d.find(b'\x78\xda')
    if i < 0: i = d.find(b'\x78\x9c')
    if i < 0:
        summary.append((os.path.basename(f), magic, 0, 0)); continue
    try:
        o = zlib.decompressobj(); raw = o.decompress(d[i:]) + o.flush()
    except Exception as e:
        summary.append((os.path.basename(f), magic, -1, 0)); continue
    name = os.path.basename(f)
    open(os.path.join(outdir, name + '.bin'),'wb').write(raw)
    strings = re.findall(rb'[\x20-\x7e]{4,}', raw)
    with open(os.path.join(outdir, name + '.strings.txt'),'wb') as fh:
        fh.write(b'\n'.join(strings))
    summary.append((name, magic, len(raw), len(strings)))
for s in summary:
    print(f"{s[0]:28s} magic={s[1]!r:10s} inflated={s[2]:>9,} strings={s[3]}")
