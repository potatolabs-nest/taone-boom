"""fc 01 b2 05 .idx — fixed-stride parser, verified on FxAsset (10 records).

Layout: 16-byte header, then FIXED-STRIDE records.
  record : env[NAMELEN+4] obfuscated name | u32 A | u32 B | u32 zero | u32 C
Obfuscation is the same self-differential family as the ca-family names:
  name[i] = env[i] ^ env[i-4] ^ name[i-4]     (derive: env[i] = paper[i] ^ name[i-4],
                                               paper[i] = env[i] ^ env[i-4])
Only name[0:4] is unknown -> derived from the record's leading directory.
"""
import os, sys, struct
from collections import Counter
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
VALID = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
DIRS = ("Game/", "Quest/", "PopupEvent/", "Item/", "Icon/", "Sound/", "Effect/",
        "Character/", "Char/", "Emo/", "Face/", "Hair/", "Body/", "Avatar/",
        "Stage/", "Data/", "Lua/", "Img/", "Texture/", "Image/", "Event/",
        "Popup/", "Cash/", "Pet/", "Npc/", "Back/", "Interface/", "Loading/",
        "Map/", "Common/", "Ui/", "UI/", "Bgm/", "Music/", "Voice/", "Font/",
        "Model/", "Anim/", "Movie/", "Wave/", "AIBattle/", "Monster/",
        "Desktop/", "Contents/", "Boom/", "Fx/", "Game", "Char")
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".dds", ".ogg", ".ani", ".scr", ".tga",
        ".luc", ".slk", ".txt", ".xml", ".cur", ".ico", ".wav", ".mp3", ".dat",
        ".ini", ".fft", ".bik", ".mod", ".msh", ".skn", ".mtr", ".eff", ".spr",
        ".bin", ".pak", ".tnt", ".json")


def decode(env, L):
    """L = plaintext name length; env must have L+4 bytes available."""
    for pfx in DIRS:
        pb = pfx.encode()
        if len(pb) < 4 or L < len(pb):
            continue
        name = bytearray(L)
        name[0:4] = pb[:4]
        ok = True
        for i in range(4, L):
            c = env[i] ^ env[i - 4] ^ name[i - 4]
            if c < 32 or c > 126:
                ok = False
                break
            name[i] = c
        if not ok:
            continue
        s = name.decode('latin1')
        if not s.startswith(pfx):
            continue
        if any(c not in VALID for c in s):
            continue
        return s
    return None


def parse(path, stride):
    d = open(path, 'rb').read()
    n = len(d)
    magic, ver, cA, cB = struct.unpack_from('<IIII', d, 0)
    recs = []
    p = 16
    while p + stride <= n:
        # trailer = last 16 bytes of the record
        t = d[p + stride - 16:p + stride]
        A, Bb, Z, C = struct.unpack('<IIII', t)
        # name = everything before the trailer
        env = d[p:p + stride - 16]
        L = len(env) - 4
        s = decode(env, L)
        recs.append((p, L, s, A, Bb, Z, C))
        p += stride
    return d, recs


for name in sys.argv[1:]:
    path = os.path.join(B, name + '.idx')
    n = os.path.getsize(path)
    print(f"=== {name}.idx {n:,}")
    for stride in range(40, 90):
        if (n - 16) % stride:
            continue
        d, recs = parse(path, stride)
        named = sum(1 for r in recs if r[2])
        if named:
            print(f"  stride={stride}: {len(recs)} recs, named={named}")
            for r in recs[:4]:
                print(f"     {r[0]:#08x} L={r[1]} ({r[3]:,},{r[4]:,},z{r[5]},c{r[6]}) {r[2]!r}")
            break
    else:
        print("  no exact stride divides the file")
