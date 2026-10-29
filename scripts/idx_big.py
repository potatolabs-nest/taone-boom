#!/usr/bin/env python3
"""Recover names from the large Fx*.idx indexes (magic ca da ef).

Transform, verified against records in both index families:

    name[i] = stem[i] ^ name[i-4]   for i >= 4
    name[i] = stem[i] ^ k           for i == 0
    name[i] = stem[i]               for 1 <= i <= 3      (PLAINTEXT)

Two consequences make this tractable:
- `stem[1:4]` is readable plaintext, so it prunes the search immediately and
  reveals the directory: FxSound begins "?P3/" (MP3/), FxMonster "?ons/"
  (Monster/), FxStage "?ame/" (Game/).
- only `k` (one byte) is unknown.

A stem is longer than its name: the name is followed by NUL padding and then
binary fields, so decode the stem, truncate at the first byte that is not a
path character, and judge THAT. Requiring the whole stem to be printable was
the earlier mistake and produced zero results.

Verified decodes:
    FxStage.idx     -> Game/AIBattle_SuperStar          (k = 0x17)
    FxMonster.idx   -> Monster/AquaMon00_Appear         (k = 0x18)
    FxSound.idx     -> MP3/Aliens                       (k = 0x0a)

Usage: python3 -I idx_big.py [--show N] [--arch NAME]
"""
import argparse, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOM = os.path.join(ROOT, "extracted/Boom")
OUT = os.path.join(ROOT, "work/idx_names_big.json")

PATHSET = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    b"0123456789_/.-")
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".dds", ".ogg", ".ani", ".scr", ".tga",
        ".luc", ".slk", ".txt", ".xml", ".cur", ".ico", ".wav", ".mp3", ".dat",
        ".ini", ".fft", ".bik", ".pcx", ".wav")


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


def name_from(decoded):
    """Truncate at the first non-path byte, then validate as a relative path."""
    end = 0
    for b in decoded:
        if b in PATHSET:
            end += 1
        else:
            break
    if end < 5:
        return None
    s = decoded[:end].decode("latin1")
    if "/" not in s or "//" in s or s[0] == "/" or s[-1] == "/":
        return None
    if "/." in s or s.endswith("."):
        return None
    return s


def candidates(data, off, maxlen=112):
    """Yield (name, k, consumed) for the stem starting at `off`."""
    n = len(data)
    if off + 6 > n:
        return
    # stem[1:4] is plaintext path text — cheap, decisive prune
    for x in data[off + 1:off + 4]:
        if x not in PATHSET:
            return
    span = data[off:min(n, off + maxlen)]
    for k in range(256):
        first = span[0] ^ k
        if not (65 <= first <= 90 or 97 <= first <= 122):
            continue
        s = name_from(decode(span, k))
        if s:
            yield s, k


def scan(data, start=16, want_ext=True):
    """Non-overlapping records left to right, longest-first."""
    out, i, n = [], start, len(data)
    seen = set()
    while i < n - 8:
        got = None
        for s, k in candidates(data, i):
            # prefer a name carrying a real extension; that is the stronger signal
            has_ext = s.lower().endswith(EXTS)
            if want_ext and not has_ext:
                continue
            got = (s, k)
            break
        if got and got[0] not in seen:
            seen.add(got[0])
            out.append((i, got[0], got[1]))
            i += len(got[0]) + 4
        else:
            i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", type=int, default=8)
    ap.add_argument("--arch")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(BOOM, "*.idx")))
    result, total, shown = {}, 0, 0
    for path in files:
        rel = os.path.basename(path)[:-4]
        if args.arch and rel != args.arch:
            continue
        data = open(path, "rb").read()
        if data[:3] != b"\xca\xda\xef":
            continue
        recs = scan(data)
        if not recs:
            continue
        result[rel] = [{"offset": off, "path": s, "k": k} for off, s, k in recs]
        total += len(recs)
        print(f"{rel:18s} {len(recs):>5,} names   ({len(data):,} B .idx)")
        for off, s, k in recs[:max(0, args.show - shown)]:
            print(f"      @{off:<7} k={k:#04x}  {s}")
            shown += 1

    if result:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(result, open(OUT, "w"), indent=1)
        print(f"\nTOTAL: {total:,} names -> {OUT}")
        if "FxSound" in result:
            ogg = sum(1 for e in result["FxSound"] if e["path"].lower().endswith(".ogg"))
            print(f"cross-check  FxSound .ogg names = {ogg}   (693 real Ogg streams exist)")


if __name__ == "__main__":
    main()
