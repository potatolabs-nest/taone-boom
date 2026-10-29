#!/usr/bin/env python3
"""Extract the real media from the index-decoded archives, with real names.

Uses work/idx_layout/walk_big.json (verified byte-exact) to pull the payloads
that are genuinely media - Ogg audio and JPEG images - and writes them under
their real in-game names, e.g. MP3/CAHero_BadBoy -> MP3__CAHero_BadBoy.ogg.

The remaining payloads are the game's own data records (sprite definitions,
avatar layer tables, map data): they begin with small little-endian integer
counts and have low entropy, so they are metadata rather than hidden media.

Usage: python3 -I extract_named_media.py [--dest DIR] [--limit-per-archive N]
"""
import argparse, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOM = os.path.join(ROOT, "extracted/Boom")
WALK = os.path.join(ROOT, "work/idx_layout/walk_big.json")


def kind(head):
    if head[:4] == b"OggS":
        return "ogg"
    if head[:3] == b"\xff\xd8\xff":
        return "jpg"
    if head[:4] == b"BM":
        return "bmp"
    if head[:4] == b"DDS ":
        return "dds"
    if head[:4] == b"\x89PNG":
        return "png"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=os.path.join(ROOT, "work/media_named"))
    ap.add_argument("--limit-per-archive", type=int)
    args = ap.parse_args()

    walk = json.load(open(WALK))
    os.makedirs(args.dest, exist_ok=True)

    counts, total, manifest = {}, 0, []
    for arch in sorted(walk):
        src = os.path.join(BOOM, arch + ".idd")
        if not os.path.exists(src):
            continue
        recs = walk[arch]["names"]
        if args.limit_per_archive:
            recs = recs[:args.limit_per_archive]
        dest = os.path.join(args.dest, arch)
        os.makedirs(dest, exist_ok=True)
        got = {}
        with open(src, "rb") as fh:
            for i, r in enumerate(recs):
                off, size, name = r["hash"], r["size_a"], r["name"]
                if size <= 0:
                    continue
                fh.seek(off)
                head = fh.read(8)
                k = kind(head)
                if not k:
                    continue
                stem = name.replace("\\", "/").strip("/").replace("/", "__")
                stem = "".join(c if c.isalnum() or c in "_-." else "_" for c in stem)
                if stem in got:
                    stem = f"{stem}_{i}"
                got[stem] = True
                out = os.path.join(dest, stem + "." + k)
                fh.seek(off)
                data = fh.read(size)
                if len(data) != size:
                    continue
                with open(out, "wb") as w:
                    w.write(data)
                counts[k] = counts.get(k, 0) + 1
                total += 1
                manifest.append({
                    "id": f"{arch}/{i:06d}", "archive": arch, "index": i,
                    "offset": off, "size": size, "format": k,
                    "mime": {"ogg": "audio/ogg", "jpg": "image/jpeg",
                             "bmp": "image/bmp", "dds": "image/vnd-ms.dds",
                             "png": "image/png"}[k],
                    "name": name,
                    "file": f"{arch}/{stem}.{k}",
                    "confidence": "high",
                })
        print(f"{arch:14s} media: {sum(1 for m in manifest if m['archive']==arch):>6,}")

    json.dump({"counts": counts, "total": total, "assets": manifest},
              open(os.path.join(args.dest, "manifest.json"), "w"),
              separators=(",", ":"))
    print(f"\nmedia files : {total:,}  {counts}")
    print(f"dest        : {args.dest}")


if __name__ == "__main__":
    main()
