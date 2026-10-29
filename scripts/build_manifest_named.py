#!/usr/bin/env python3
"""Build a fully-named asset manifest from the decoded .idx index.

Uses work/idx_layout/walk_big.json, which describes every entry of all 12
archives: real name, cumulative offset (`hash`), and exact byte length
(`size_a`). Verified independently: sum(size_a) == .idd size on all 12 archives,
the offset chain is unbroken, and reassembling a .idd from its payloads
reproduces the original byte for byte (SHA-256 match).

Each payload's format is detected from its own magic bytes, because the game
names carry no extension - the directory implies the type (MP3/ is audio,
Game/ is textures, Map/ is map data).

Usage: python3 -I build_manifest_named.py [--extract] [--limit N]
"""
import argparse, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOM = os.path.join(ROOT, "extracted/Boom")
WALK = os.path.join(ROOT, "work/idx_layout/walk_big.json")
OUTDIR = os.path.join(ROOT, "work/assets_named")
OUTMAN = os.path.join(OUTDIR, "manifest.json")

# magic -> (extension, mime)
MAGICS = [
    (b"OggS",            "ogg",  "audio/ogg"),
    (b"DDS ",            "dds",  "image/vnd-ms.dds"),
    (b"BM",              "bmp",  "image/bmp"),
    (b"\x89PNG\r\n",     "png",  "image/png"),
    (b"\xff\xd8\xff",    "jpg",  "image/jpeg"),
    (b"RIFF",            "wav",  "audio/wav"),
    (b"GIF8",            "gif",  "image/gif"),
    (b"BZh",             "bz2",  "application/x-bzip2"),
    (b"\x1bLua",         "luc",  "application/x-lua"),
    (b"PACK",            "pak",  "application/octet-stream"),
]


def detect(head):
    for m, ext, mime in MAGICS:
        if head[:len(m)] == m:
            return ext, mime
    if head[:2] == b"\x78\xda" or head[:2] == b"\x78\x9c":
        return "zlib", "application/zlib"
    return "bin", "application/octet-stream"


def safe_name(path):
    """Filesystem-safe filename from an in-archive path."""
    p = path.replace("\\", "/").strip("/")
    p = re.sub(r"[^A-Za-z0-9_./-]", "_", p)
    p = p.replace("/", "__")
    return p or "unnamed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true",
                    help="also write the payload files (large: ~1.1 GB)")
    ap.add_argument("--limit", type=int, help="cap entries per archive (testing)")
    args = ap.parse_args()

    if not os.path.exists(WALK):
        sys.exit("missing " + WALK)
    walk = json.load(open(WALK))

    assets, archives = [], []
    by_archive = {}
    by_format = {}
    dupes = 0

    for arch in sorted(walk):
        idd_path = os.path.join(BOOM, arch + ".idd")
        if not os.path.exists(idd_path):
            continue
        recs = walk[arch]["names"]
        if args.limit:
            recs = recs[:args.limit]
        dest = os.path.join(OUTDIR, arch)
        if args.extract:
            os.makedirs(dest, exist_ok=True)

        seen = {}
        count = 0
        with open(idd_path, "rb") as fh:
            for i, r in enumerate(recs):
                off, size, name = r["hash"], r["size_a"], r["name"]
                if size <= 0:
                    continue
                fh.seek(off)
                head = fh.read(16)
                fmt, mime = detect(head)
                stem = safe_name(name)
                if stem in seen:
                    dupes += 1
                    stem = f"{stem}_{i}"
                seen[stem] = True
                rel = f"{arch}/{stem}.{fmt}"
                if args.extract:
                    fh.seek(off)
                    data = fh.read(size)
                    if len(data) == size:
                        with open(os.path.join(OUTDIR, rel), "wb") as out:
                            out.write(data)
                assets.append({
                    "id": f"{arch}/{i:06d}",
                    "archive": arch,
                    "index": i,
                    "offset": off,
                    "size": size,
                    "format": fmt,
                    "mime": mime,
                    "name": name,          # the real name, extension-less
                    "file": rel,
                    "confidence": "high",
                })
                count += 1
                by_format[fmt] = by_format.get(fmt, 0) + 1
        by_archive[arch] = count
        archives.append({"name": arch, "idd_size": os.path.getsize(idd_path),
                         "asset_count": count})
        print(f"{arch:16s} {count:>7,} entries")

    manifest = {
        "generated": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "index-decoded, verified byte-exact (SHA-256 round trip)",
        "summary": {"total_assets": len(assets), "by_format": by_format,
                    "by_archive": by_archive, "ui_sprites": 0, "ndadata_pak": 0},
        "archives": archives,
        "assets": assets,
        "ui_sprites": [],
        "ndadata": [],
    }
    os.makedirs(OUTDIR, exist_ok=True)
    json.dump(manifest, open(OUTMAN, "w"), separators=(",", ":"))
    print(f"\nentries      : {len(assets):,}")
    print(f"by format    : {by_format}")
    print(f"duplicate stems disambiguated: {dupes}")
    print(f"manifest     : {OUTMAN}  ({os.path.getsize(OUTMAN)/1e6:.1f} MB)")
    if args.extract:
        print(f"files written: {OUTDIR}")


if __name__ == "__main__":
    main()
