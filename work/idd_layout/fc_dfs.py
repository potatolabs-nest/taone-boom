"""DFS the fc-family record chain: find the name length at each record that
decodes to a valid path AND lets the chain continue to EOF."""
import os, sys
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
VALID = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
DIRS = ("Game/", "Quest/", "PopupEvent/", "Item/", "Icon/", "Sound/", "Effect/",
        "Character/", "Char/", "Emo/", "Face/", "Hair/", "Body/", "Avatar/",
        "Stage/", "Data/", "Lua/", "Img/", "Texture/", "Image/", "Event/",
        "Popup/", "Cash/", "Pet/", "Npc/", "Back/", "Interface/", "Loading/",
        "Map/", "Common/", "Ui/", "UI/", "Bgm/", "Music/", "Voice/", "Font/",
        "Model/", "Anim/", "Movie/", "Wave/", "AIBattle/", "Monster/",
        "Desktop/", "Contents/", "Boom/", "Fx/", "Game", "Char", "Sound")
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".dds", ".ogg", ".ani", ".scr", ".tga",
        ".luc", ".slk", ".txt", ".xml", ".cur", ".ico", ".wav", ".mp3", ".dat",
        ".ini", ".fft", ".bik", ".mod", ".msh", ".skn", ".mtr", ".eff", ".spr",
        ".bin", ".pak", ".tnt", ".json")


def decode(env, L):
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
        if not s.lower().endswith(EXTS):
            continue
        return s
    return None


def solve(d):
    n = len(d)
    memo = {}

    def go(p, depth):
        if p == n:
            return []
        if p > n or depth > 60000:
            return None
        if (p, depth) in memo:
            return None
        for L in range(6, 400):
            if p + L + 20 > n:
                break
            s = decode(d[p:p + L + 4], L)
            if s is None:
                continue
            sub = go(p + L + 16, depth + 1)
            if sub is not None:
                return [(p, L, s)] + sub
        memo[(p, depth)] = 1
        return None

    return go(16, 0)


for name in sys.argv[1:]:
    d = open(os.path.join(B, name + '.idx'), 'rb').read()
    r = solve(d)
    print(f"=== {name}.idx {len(d):,}  solved={r is not None}")
    if r:
        for p, L, s in r[:8]:
            print(f"   {p:#08x} L={L:3d} {s!r}")
        print(f"   ... {len(r)} records")
        for p, L, s in r[-3:]:
            print(f"   {p:#08x} L={L:3d} {s!r}")
        print(f"   end={r[-1][0]+r[-1][1]+16:#x} file={len(d):#x} exact={r[-1][0]+r[-1][1]+16==len(d)}")
