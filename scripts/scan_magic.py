import sys, collections
magics = {
 b'DDS ': 'dds', b'BM': 'bmp', b'JFIF': 'jpg', b'PNG': 'png', b'OggS': 'ogg',
 b'RIFF': 'riff/wav', b'ID3': 'mp3', b'BZh': 'bzip2', b'\x78\x9c':'zlib',
 b'\x78\xda':'zlib', b'GIF8':'gif', b'\xff\xd8\xff':'jpg-soi', b'UnityWeb':'unity',
 b'KTX':'ktx', b'\x1f\x8b':'gzip', b'ftyp':'mp4', b'BC\x00':'bc', b'\x00\x00\x02\x00':'tga?',
}
for p in sys.argv[1:]:
    d = open(p,'rb').read()
    c = collections.Counter()
    for m,name in magics.items():
        i=0
        while True:
            i = d.find(m,i)
            if i<0: break
            c[name]+=1; i+=1
    print(p, len(d), dict(c.most_common()))
