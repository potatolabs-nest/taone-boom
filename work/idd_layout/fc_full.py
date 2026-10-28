"""Direct parser for the fc 01 b2 05 .idx family (CharTE, EmoTE, FxAsset, ndadata).

Record layout (verified):
    header   : u32 magic | u32 ver=15 | u32 countA | u32 countB      (16 bytes)
    record   : name[namelen] obfuscated | u32 sizeA | u32 sizeB | u32 zero | u32 NEXT_namelen
    next record's name follows immediately.

The name obfuscation is  env[i] = paper[i] ^ name[i-4], paper global per file,
so   name[i] = env[i] ^ env[i-4] ^ name[i-4]  for i>=4
and only name[0:4] is unknown - derived from the record's leading directory.

Record 0's namelen is not stored; it is found by requiring the trailer's last
u32 to be a plausible next namelen AND the name to decode to a real path.
"""
import os, sys, struct, json
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
VALID = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
DIRS = ("Game/", "Quest/", "PopupEvent/", "Item/", "Icon/", "Sound/", "Effect/",
        "Character/", "Char/", "Emo/", "Face/", "Hair/", "Body/", "Avatar/",
        "Stage/", "Data/", "Lua/", "Img/", "Texture/", "Image/", "Event/",
        "Popup/", "Cash/", "Pet/", "Npc/", "Back/", "Interface/", "Loading/",
        "Map/", "Common/", "Ui/", "UI/", "Bgm/", "Music/", "Voice/", "Font/",
        "Model/", "Anim/", "Movie/", "Wave/", "AIBattle/", "Monster/",
        "Desktop/", "Contents/", "Sound2/", "Boom/", "Fx/", "DX/")
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".dds", ".ogg", ".ani", ".scr", ".tga",
        ".luc", ".slk", ".txt", ".xml", ".cur", ".ico", ".wav", ".mp3", ".dat",
        ".ini", ".fft", ".bik", ".mod", ".msh", ".skn", ".mtr", ".eff", ".spr",
        ".bin", ".pak")


def decode_name(env, L):
    """env[0:L] obfuscated; needs env[L:L+4] for the look-ahead form."""
    for pfx in DIRS:
        pb = pfx.encode()
        if len(pb) < 4 or L < len(pb):
            continue
        name = bytearray(L)
        name[0:4] = [env[i] ^ env[i] ^ b for i, b in zip(range(4), pb[:4])]
        name[0:4] = list(pb[:4])
        # name[i] = env[i] ^ env[i-4] ^ name[i-4]
        ok = True
        for i in range(4, L):
            c = env[i] ^ env[i - 4] ^ name[i - 4]
            if c == 0 or c > 126 or c < 32:
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
        if len(s) < 6:
            continue
        return s
    return None


def parse(path):
    d = open(path, 'rb').read()
    n = len(d)
    magic, ver, cA, cB = struct.unpack_from('<IIII', d, 0)
    if magic != 0x05b201fc:
        return None
    # find record 0 namelen
    p = 16
    L = None
    for cand in range(6, 300):
        if cand + 16 > n:
            break
        nxt = struct.unpack_from('<I', d, cand + 12)[0]
        if not (6 <= nxt <= 300):
            continue
        s = decode_name(d[p:p + cand + 8], cand)
        if s:
            L = cand
            break
    if L is None:
        return None, p, n
    recs = []
    while p + L + 16 <= n:
        env = d[p:p + L + 8]
        s = decode_name(env, L)
        sizeA, sizeB, zero, nxt = struct.unpack_from('<IIII', d, p + L)
        recs.append((p, L, s, sizeA, sizeB, zero))
        p = p + L + 16
        L = nxt
        if not (1 <= L <= 300):
            break
    return recs, p, n


if __name__ == '__main__':
    for name in sys.argv[1:]:
        r = parse(os.path.join(B, name + '.idx'))
        if r is None:
            print(f"{name}: not fc family")
            continue
        recs, p, n = r
        print(f"{name}.idx {n:,}: records={len(recs)} end={p:#x} ({p}) exact={p==n}")
        named = sum(1 for x in recs if x[2])
        print(f"  named={named}/{len(recs)}")
        for x in recs[:6]:
            print(f"   {x[0]:#08x} L={x[1]:3d} sizes=({x[3]:,},{x[4]:,}) zero={x[5]} {x[2]!r}")
        from collections import Counter
        print("  sizeA==sizeB:", sum(1 for x in recs if x[3] == x[4]), "/", len(recs))
        print("  zero==0:", sum(1 for x in recs if x[5] == 0), "/", len(recs))
        print("  sum sizeA:", f"{sum(x[3] for x in recs):,}")
        print("  sum sizeB:", f"{sum(x[4] for x in recs):,}")
