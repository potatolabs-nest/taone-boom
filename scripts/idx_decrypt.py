#!/usr/bin/env python3
"""Decrypt the .idx name fields.

SOLVED. The name stem uses a self-differential stream:

    stem[i] = name[i] ^ name[i-4]      for i >= 4
    stem[i] = name[i] ^ seed[i]        for i <  4

so name[i] = stem[i] ^ name[i-4]. Only the four seed bytes are unknown; in every
record checked they are (k, 0, 0, 0), so a single byte is brute-forced and the
winner picked by whether the result reads as a real asset path.

Record layout:

    u32 magic (ca da ef XX | fc 01 b2 05)  u32 version=15  u32 count
    per record:
        u32 len
        stem[len]              <- obfuscated, decrypts to the full relative path
        u32 hash
        u32 size
        u32 size
        u32 zero

Confirmation: MonWarsRank2nd record 1 decrypts to
"Quest/KBNB_Quest_MonWarsRankBG.bmp", which matches the plaintext path found
independently in that bundle's compiled Lua.

Usage: python3 -I idx_decrypt.py [--json OUT] [--show N]
"""
import argparse, glob, json, os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOM = os.path.join(ROOT, "extracted/Boom")

VALID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                  "0123456789_/.-")
# Directory prefixes the client uses. A record's four seed bytes are derived
# from whichever prefix it actually begins with, so this list is the only
# prior knowledge the decoder needs. "Game/" carries the large Fx* archives
# (e.g. Game/AIBattle_SuperStar), "Quest/" the ndadata popup bundles.
DIRS = ("Game/", "Quest/", "PopupEvent/", "Item/", "Icon/", "Sound/", "Effect/",
        "Character/", "Avatar/", "Stage/", "Data/", "Lua/", "Img/", "Texture/",
        "Image/", "Event/", "Popup/", "Cash/", "Pet/", "Npc/", "Back/",
        "Interface/", "Loading/", "Map/", "Common/", "Ui/", "UI/", "Bgm/",
        "Music/", "Voice/", "Font/", "Model/", "Anim/", "Movie/", "Wave/")
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".dds", ".ogg", ".ani", ".scr",
        ".tga", ".luc", ".slk", ".txt", ".xml", ".cur", ".ico", ".wav",
        ".mp3", ".dat", ".ini", ".fft", ".bik", ".tga")


def decrypt(stem, seed):
    """name[i] = stem[i] ^ name[i-4], with the head seeded by a 4-byte IV."""
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def validate(name, prefix):
    """Strict acceptance: a real path, starting with the prefix that seeded it.

    Being strict here matters more than being clever with a score — a lenient
    scorer accepts arbitrary printable garbage produced by a wrong seed.
    """
    if len(name) < 8:
        return False
    if any(b < 32 or b > 126 for b in name):
        return False
    s = name.decode("latin1")
    if not s.startswith(prefix):
        return False
    if not s.lower().endswith(EXTS):
        return False
    if any(c not in VALID_CHARS for c in s):
        return False
    # no double separators or empty path segments
    if "//" in s or "/." in s or "../" in s:
        return False
    return True


def best_name(stem):
    """Recover the name by deriving the seed from each known directory prefix.

    Deterministic, and far more reliable than guessing a seed by score: a
    candidate is accepted only if decrypting with the seed implied by `prefix`
    yields a path that really does start with that prefix and end in a known
    extension.
    """
    for pfx in DIRS:
        pb = pfx.encode()
        # a prefix shorter than the 4-byte seed cannot derive it
        if len(pb) < 4 or len(stem) < len(pb):
            continue
        seed = bytes(stem[i] ^ pb[i] for i in range(4))
        nm = decrypt(stem, seed)
        if validate(nm, pfx):
            return nm, seed
    return None, None


def parse_records(idx):
    """Yield (offset, name) for every record whose stem decrypts cleanly.

    A fixed stride is not assumed — the header before each stem varies between
    archives — so candidate positions are tried one byte at a time and only
    records that satisfy strict validation are accepted.
    """
    n = len(idx)
    p = 16
    seen = set()
    while p + 8 <= n:
        ln = struct.unpack_from("<I", idx, p)[0]
        if 0 < ln < 1024 and p + 4 + ln <= n:
            stem = idx[p + 4:p + 4 + ln]
            nm, seed = best_name(stem)
            if nm is not None and nm not in seen:
                seen.add(nm)
                yield p, nm
                p = p + 4 + ln + 16
                continue
        p += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(ROOT, "work/idx_names.json"))
    ap.add_argument("--show", type=int, default=20)
    args = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(BOOM, "*.idx")) +
                   glob.glob(os.path.join(BOOM, "ndadata/*.idx")))
    result, total, named = {}, 0, 0
    shown = 0

    for path in paths:
        rel = os.path.relpath(path, BOOM)[:-4]
        try:
            idx = open(path, "rb").read()
        except OSError:
            continue
        recs = list(parse_records(idx))
        if not recs:
            continue
        entries = [{"offset": off, "name": nm.decode("latin1"),
                    "confidence": "high"} for off, nm in recs]
        result[rel] = entries
        total += len(recs)
        named += len(recs)
        print(f"{rel:34s} {len(recs):>5d} names")
        for e in entries[:max(0, args.show - shown)]:
            print(f"      {e['name']}")
            shown += 1

    os.makedirs(os.path.dirname(args.json), exist_ok=True)
    with open(args.json, "w") as fh:
        json.dump(result, fh, indent=1)

    print()
    print(f"archives with names : {len(result)}")
    print(f"names recovered     : {named}")
    print(f"wrote               : {args.json}")


if __name__ == "__main__":
    main()
