"""Fast direct parser for the fc 01 b2 05 .idx family (CharTE / EmoTE).

Documented layout (NOTES.md §8):
    u32 magic | u32 version=15 | u32 count
    per record: u32 len | stem[len] | u32 hash | u32 size | u32 size | u32 zero

That is an 8-byte header prefix in the .idd (4-byte len + 4 counters).
"""
import os, sys, struct
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
VALID = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
DIRS = ("Game/", "Quest/", "PopupEvent/", "Item/", "Icon/", "Sound/", "Effect/",
        "Character/", "Avatar/", "Stage/", "Data/", "Lua/", "Img/", "Texture/",
        "Image/", "Event/", "Popup/", "Cash/", "Pet/", "Npc/", "Back/",
        "Interface/", "Loading/", "Map/", "Common/", "Ui/", "UI/", "Bgm/",
        "Music/", "Voice/", "Font/", "Model/", "Anim/", "Movie/", "Wave/",
        "Char/", "Emo/", "Face/", "Hair/", "Body/")
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".dds", ".ogg", ".ani", ".scr", ".tga",
        ".luc", ".slk", ".txt", ".xml", ".cur", ".ico", ".wav", ".mp3", ".dat",
        ".ini", ".fft", ".bik", ".mod", ".msh", ".skn", ".mtr", ".eff", ".spr")


def decrypt(stem, seed):
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def best_name(stem):
    for pfx in DIRS:
        pb = pfx.encode()
        if len(pb) < 4 or len(stem) < len(pb):
            continue
        seed = bytes(stem[i] ^ pb[i] for i in range(4))
        nm = decrypt(stem, seed)
        s = nm.decode('latin1')
        if not s.startswith(pfx):
            continue
        if not s.lower().endswith(EXTS):
            continue
        if any(c not in VALID for c in s):
            continue
        if '//' in s or '/.' in s or len(s) < 8:
            continue
        return s, seed
    return None, None


name = sys.argv[1]
d = open(os.path.join(B, name + '.idx'), 'rb').read()
n = len(d)
magic, ver, cnt, cnt2 = struct.unpack_from('<IIII', d, 0)
print(f"{name}.idx  size={n:,}  magic={magic:#x}  ver={ver}  counts={cnt},{cnt2}")
p = 16
recs = []
while p + 8 <= n:
    ln = struct.unpack_from('<I', d, p)[0]
    if not (0 < ln < 1024 and p + 8 + ln <= n):
        print(f"  stop: bad len {ln} at {p:#x}")
        break
    stem = d[p + 4:p + 4 + ln]
    nm, seed = best_name(stem)
    f = struct.unpack_from('<IIII', d, p + 4 + ln)
    recs.append((p, ln, nm, f))
    if len(recs) <= 5:
        print(f"  {p:#08x} len={ln:3d} fields={f}  {nm!r}")
    p = p + 4 + ln + 16
print(f"  parsed {len(recs)} records  end={p:#x} ({p})  filesize={n:#x}  exact={p==n}")
named = sum(1 for r in recs if r[2])
print(f"  named: {named}/{len(recs)}")
tot = sum(r[3][1] for r in recs)
print(f"  sum(field1): {tot:,}")
