import sys, os, glob
pats = {b'\xca\xda\xef':'magic_cadaef', b'ssi1':'ssi1', b'.idd':'.idd', b'.idx':'.idx', b'CryptGenRandom':'crypto'}
for f in sorted(glob.glob(sys.argv[1])):
    d = open(f,'rb').read()
    hits = {n: d.count(p) for p,n in pats.items() if d.count(p)}
    if hits:
        print(f"{os.path.basename(f):28s} {os.path.getsize(f):>10,}  {hits}")
