#!/usr/bin/env python3
"""Recover names from the large Fx*.idx indexes (magic ca da ef).

Transform (verified on FxStage record 0 -> "Game/AIBattle_SuperStar"):
    name[i] = stem[i] ^ name[i-4]   for i >= 4
    name[i] = stem[i] ^ k           for i == 0
    name[i] = stem[i]               for 1 <= i <= 3      (plaintext)
so only `k` is unknown, and `stem[1:4]` is readable path text.

The record framing is not fully pinned down, so this does NOT assume a stride.
It scans for candidate stems and keeps any that decode to a real path, which is
robust to the framing being wrong. Records are taken non-overlapping, left to
right, longest match first.

Usage: python3 -I idx_big.py [--show N]
"""
import argparse, glob, json, os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOM = os.path.join(ROOT, "extracted/Boom")
OUT = os.path.join(ROOT, "work/idx_names_big.json")

PATHCHARS = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                      b"0123456789_/.-")
DIRS = ("Game/", "Quest/", "PopupEvent/", "Item/", "Icon/", "Sound/", "Effect/",
        "Character/", "Avatar/", "Stage/", "Data/", "Lua/", "Img/", "Texture/",
        "Image/", "Event/", "Popup/", "Cash/", "Pet/", "Npc/", "Back/",
        "Interface/", "Loading/", "Map/", "Common/", "Bg/", "Model/", "Anim/",
        "Font/", "Music/", "Voice/", "Movie/", "Wave/", "Ui/")
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".dds", ".ogg", ".ani", ".scr", ".tga",
        ".luc", ".slk", ".txt", ".xml", ".cur", ".ico", ".wav", ".mp3", ".dat",
        ".ini", ".fft", ".bik", ".pcx")


def decode(stem, k):
    out = bytearray(len(stem))
    for i in range(len(stem)):
        if i == 0:
            out[i] = stem[i] ^ k
        elif i < 4:
            out[i] = stem[i]
        else:
            out[i] = stem[i] ^ out[i - 4]
    return bytes(out)


def valid_path(b):
    """Strict: path chars only, has a separator, ends in a known extension,
    and begins with a directory this client uses."""
    if len(b) < 10:
        return None
    for x in b:
        if x not in PATHCHARS:
            return None
    if b[0] == 0x2F or b[-1] == 0x2F:
        return None
    s = b.decode("latin1")
    if "//" in s or "/." in s:
        return None
    low = s.lower()
    if not low.endswith(EXTS):
        return None
    for d in DIRS:
        if s.startswith(d):
            return s
    return None


def try_at(data, off):
    """Best (name, k, length) for a stem starting at `off`, or None.

    Prunes hard first: stem[1:4] is plaintext path text, so reject quickly on
    that before doing any 256-way search.
    """
    n = len(data)
    if off + 10 > n:
        return None
    for x in data[off + 1:off + 4]:
        if x not in PATHCHARS:
            return None
    # first byte must decode to a letter for a real path
    best = None
    for L in range(n - off, 9, -1):
        if off + L > n:
            continue
        stem = data[off:off + L]
        for k in range(256):
            first = stem[0] ^ k
            if not (65 <= first <= 90 or 97 <= first <= 122):
                continue
            s = valid_path(decode(stem, k))
            if s:
                return s, k, L
        if L > 96:
            break            # paths here are short; stop early once too long
    return None


def scan(data, start=16):
    """Non-overlapping records, left to right, taking the longest valid match."""
    out = []
    i = start
    n = len(data)
    while i < n - 12:
        r = try_at(data, i)
        if r:
            s, k, L = r
            out.append((i, s, k, L))
            i += L
        else:
            i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", type=int, default=10)
    args = ap.parse_args()

    result, total, shown = {}, 0, 0
    for path in sorted(glob.glob(os.path.join(BOOM, "*.idx"))):
        rel = os.path.basename(path)[:-4]
        data = open(path, "rb").read()
        if data[:3] != b"\xca\xda\xef":
            continue
        recs = scan(data)
        if not recs:
            continue
        # de-duplicate on path, keeping the first offset
        seen, uniq = set(), []
        for off, s, k, L in recs:
            if s in seen:
                continue
            seen.add(s)
            uniq.append({"offset": off, "path": s, "k": k})
        result[rel] = uniq
        total += len(uniq)
        print(f"{rel:18s} {len(uniq):>5,} names")
        for e in uniq[:max(0, args.show - shown)]:
            print(f"      {e['path']}")
            shown += 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(result, open(OUT, "w"), indent=1)
    print(f"\nTOTAL: {total:,} names -> {OUT}")
    if "FxSound" in result:
        ogg = sum(1 for e in result["FxSound"] if e["path"].lower().endswith(".ogg"))
        print(f"cross-check: FxSound .ogg names = {ogg} (693 Ogg streams exist)")


if __name__ == "__main__":
    main()
