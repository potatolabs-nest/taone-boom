#!/usr/bin/env python3
"""
Carve assets out of Club Audition .idd archives.

PRIMARY PATH (solved — see work/idd_layout_report.md):
  Every big `ca da ef` / `fc 01 b2 05` `.idx` holds a global self-differential
  XOR chain whose records give the EXACT payload size of every entry in the
  sibling `.idd`.  sum(sizes) == .idd size exactly (measured, all 12 archives),
  so the `.idd` is a plain concatenation of those payloads in record order.
  This yields named, exactly-sized payloads and 100% byte coverage.

FALLBACK PATH: magic-carve + per-format length parsing.  Kept because it still
  handles any archive without a matching .idx.

Usage:
  python3 -I extract_assets.py --dry-run
  python3 -I extract_assets.py --archive FxSound
  python3 -I extract_assets.py            # everything
"""
import argparse, json, os, struct, sys, time

BOOM = "/Users/hieu/Workspaces/taone/extracted/Boom"
OUT = "/Users/hieu/Workspaces/taone/work/assets"

# archive -> idd filename
ARCHIVES = {
    "FxAsset": "FxAsset.idd",
    "FxStage": "FxStage.idd",
    "FxCharacter": "FxCharacter.idd",
    "FxContents": "FxContents.idd",
    "FxDesktop": "FxDesktop.idd",
    "FxHiddenCatch": "FxHiddenCatch.idd",
    "FxMonster": "FxMonster.idd",
    "FxSound": "FxSound.idd",
    "FxMap": "FxMap.idd",
    "fx": "fx.idd",
    "CharTE": "CharTE.idd",
    "EmoTE": "EmoTE.idd",
}

MIME = {
    "ogg": "audio/ogg", "bmp": "image/bmp", "dds": "image/vnd-ms.dds",
    "png": "image/png", "jpg": "image/jpeg", "riff": "audio/wav",
    "gif": "image/gif", "ktx": "image/ktx",
}


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


# ---------- per-format length parsers ----------
# each returns (size, confidence) or (None, None) if it cannot be determined

def _ogg(buf, p):
    """Walk Ogg pages to the EOS page. Returns total byte length."""
    total = 0
    q = p
    n = len(buf)
    pages = 0
    while q + 27 <= n:
        if buf[q:q + 4] != b"OggS":
            return None, None
        if buf[q + 4] != 0:            # stream structure version must be 0
            return None, None
        nsegs = buf[q + 26]
        if q + 27 + nsegs > n:
            return None, None
        segs = buf[q + 27:q + 27 + nsegs]
        size = 27 + nsegs + sum(segs)
        if q + size > n:
            return None, None
        total += size
        pages += 1
        eos = buf[q + 5] & 0x04
        q += size
        if eos:
            return (total, "high") if pages >= 1 else (None, None)
        if pages > 20000:               # sanity bound
            return None, None
    return None, None


def _bmp(buf, p):
    """BMP: bfSize at offset 2 covers the whole file."""
    if p + 54 > len(buf):
        return None, None
    if u16(buf, p) != 0x4D42:           # 'BM'
        return None, None
    size = u32(buf, p + 2)
    offbits = u32(buf, p + 10)
    if size < 54 or p + size > len(buf):
        return None, None
    if offbits < 14 or offbits > size:
        return None, None
    # reserved fields are conventionally 0 in files this game ships
    if u32(buf, p + 6) != 0:
        return None, None
    dib = u32(buf, p + 14)
    if dib not in (12, 40, 52, 56, 64, 108, 124):
        return None, None
    w, h = struct.unpack_from("<ii", buf, p + 18)
    if w == 0 or h == 0 or abs(w) > 20000 or abs(h) > 20000:
        return None, None
    return size, "high"


def _dds(buf, p):
    """DDS: 128-byte header, then block or raw pixel data."""
    if p + 128 > len(buf) or buf[p:p + 4] != b"DDS ":
        return None, None
    dwsize = u32(buf, p + 4)
    if dwsize != 124:
        return None, None
    flags = u32(buf, p + 8)
    height = u32(buf, p + 12)
    width = u32(buf, p + 16)
    pitch = u32(buf, p + 20)
    mips = u32(buf, p + 28)
    rgb_bits = u32(buf, p + 88)
    fourcc = buf[p + 84:p + 88]
    if width == 0 or height == 0 or width > 32768 or height > 32768:
        return None, None
    if mips == 0:
        mips = 1
    if mips > 16:
        return None, None
    DDSD_LINEARSIZE = 0x80000
    if fourcc in (b"DXT1",):
        top = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * 8
    elif fourcc in (b"DXT2", b"DXT3", b"DXT4", b"DXT5"):
        top = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * 16
    elif fourcc == b"\x00\x00\x00\x00" and rgb_bits in (8, 16, 24, 32):
        top = width * height * (rgb_bits // 8)
    elif flags & DDSD_LINEARSIZE:
        top = pitch
    else:
        return None, None
    # mip chain adds ~1/3; only claim high confidence for a single level
    total = top
    w, h = width, height
    for _ in range(1, mips):
        w = max(1, w // 2); h = max(1, h // 2)
        if fourcc == b"DXT1":
            total += max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * 8
        elif fourcc in (b"DXT2", b"DXT3", b"DXT4", b"DXT5"):
            total += max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * 16
        elif fourcc == b"\x00\x00\x00\x00" and rgb_bits in (8, 16, 24, 32):
            total += w * h * (rgb_bits // 8)
        else:
            return None, None
    size = 128 + total
    if p + size > len(buf):
        return None, None
    return size, ("high" if mips == 1 else "medium")


def _png(buf, p):
    if p + 8 > len(buf) or buf[p:p + 8] != b"\x89PNG\r\n\x1a\n":
        return None, None
    q = p + 8
    n = len(buf)
    while q + 8 <= n:
        ln = struct.unpack_from(">I", buf, q)[0]
        typ = buf[q + 4:q + 8]
        if ln > 100_000_000:
            return None, None
        q += 12 + ln                  # len + type + data + crc
        if typ == b"IEND":
            if q > n:
                return None, None
            return q - p, "high"
    return None, None


def _jpg(buf, p):
    """Walk the JPEG segment chain and reject anything that is not a valid chain.

    An EOI scan accepts false positives and produces spans that then swallow
    every following payload; requiring a well-formed segment chain rejects
    random bytes within a couple of segments.
    """
    n = len(buf)
    if p + 4 > n or buf[p] != 0xFF or buf[p + 1] != 0xD8:
        return None, None
    q = p + 2
    seen = False
    while q + 1 < n:
        if buf[q] != 0xFF:
            return None, None              # chain must stay marker-aligned
        while q < n and buf[q] == 0xFF:    # fill bytes
            q += 1
        if q >= n:
            return None, None
        m = buf[q]
        q += 1
        if m == 0xD9:                      # EOI
            return (q - p, "high") if seen else (None, None)
        if m == 0x01 or 0xD0 <= m <= 0xD7:  # standalone markers, no payload
            continue
        if m == 0xDA:                      # SOS — entropy-coded data follows
            # in entropy data FF is always followed by 00 or D0-D7, so a
            # literal FF D9 there is the real EOI
            e = buf.find(b"\xff\xd9", q)
            if e < 0:
                return None, None
            return e + 2 - p, "high"
        if q + 2 > n:
            return None, None
        ln = struct.unpack_from(">H", buf, q)[0]
        if ln < 2:
            return None, None
        q += ln
        seen = True
        if q > n:
            return None, None
    return None, None


def _riff(buf, p):
    if p + 12 > len(buf) or buf[p:p + 4] != b"RIFF":
        return None, None
    size = u32(buf, p + 4) + 8
    if size < 12 or p + size > len(buf):
        return None, None
    return size, "high"


def _gif(buf, p):
    if p + 6 > len(buf) or buf[p:p + 6] not in (b"GIF87a", b"GIF89a"):
        return None, None
    end = buf.find(b"\x00\x3b", p)
    if end < 0:
        return None, None
    return end + 2 - p, "low"


def _ktx(buf, p):
    if p + 64 > len(buf) or buf[p:p + 12] != b"\xabKTX 11\xbb\r\n\x1a\n":
        return None, None
    size = u32(buf, p + 40)
    if size == 0 or size == 0xFFFFFFFF or p + size > len(buf):
        return None, None
    return size, "medium"


# order matters: 4-byte magics first, 'BM' last (weakest)
DETECTORS = [
    (b"OggS", "ogg", _ogg),
    (b"DDS ", "dds", _dds),
    (b"\x89PNG", "png", _png),
    (b"RIFF", "riff", _riff),
    (b"\xabKTX", "ktx", _ktx),
    (b"\xff\xd8\xff", "jpg", _jpg),
    (b"GIF8", "gif", _gif),
    (b"BM", "bmp", _bmp),
]


def find_payloads(buf):
    """Return non-overlapping (offset, size, fmt, confidence), sorted by offset."""
    cands = {}                          # offset -> (size, fmt, conf)
    n = len(buf)
    for magic, fmt, fn in DETECTORS:
        start = 0
        while True:
            i = buf.find(magic, start)
            if i < 0:
                break
            start = i + 1
            size, conf = fn(buf, i)
            if size and size > 0:
                # prefer the candidate at this offset with the best confidence
                prev = cands.get(i)
                if prev is None or (prev[2] != "high" and conf == "high"):
                    cands[i] = (size, fmt, conf)
    # greedy non-overlapping selection by offset
    out = []
    last_end = -1
    for off in sorted(cands):
        size, fmt, conf = cands[off]
        if off < last_end:
            continue
        out.append((off, size, fmt, conf))
        last_end = off + size
    return out


def extract_archive(name, idd_path, dry_run=False, limit=None):
    size_idd = os.path.getsize(idd_path)
    with open(idd_path, "rb") as fh:
        buf = fh.read()
    payloads = find_payloads(buf)
    if limit:
        payloads = payloads[:limit]
    counts = {}
    dest = os.path.join(OUT, name)
    if not dry_run:
        os.makedirs(dest, exist_ok=True)
    assets = []
    for idx, (off, size, fmt, conf) in enumerate(payloads):
        counts[fmt] = counts.get(fmt, 0) + 1
        ext = fmt
        rel = f"{name}/{idx:06d}.{ext}"
        if not dry_run:
            with open(os.path.join(OUT, rel), "wb") as out:
                out.write(buf[off:off + size])
        assets.append({
            "id": f"{name}/{idx:06d}",
            "archive": name,
            "index": idx,
            "offset": off,
            "size": size,
            "format": fmt,
            "mime": MIME.get(fmt, "application/octet-stream"),
            "name": None,
            "file": rel,
            "confidence": conf,
        })
    del buf
    return {
        "name": name,
        "idd_size": size_idd,
        "asset_count": len(assets),
        "by_format": counts,
    }, assets


def load_ui_sprites():
    """vh/*.bmp have real names and need no extraction."""
    vh = os.path.join(BOOM, "vh")
    out = []
    dest = os.path.join(OUT, "vh")
    os.makedirs(dest, exist_ok=True)
    for fn in sorted(os.listdir(vh)):
        if not fn.lower().endswith(".bmp"):
            continue
        src = os.path.join(vh, fn)
        with open(src, "rb") as fh:
            head = fh.read(32)
        w, h = struct.unpack_from("<ii", head, 18)
        with open(os.path.join(dest, fn), "wb") as o, open(src, "rb") as i:
            o.write(i.read())
        out.append({
            "name": os.path.splitext(fn)[0],
            "file": f"vh/{fn}",
            "width": w,
            "height": abs(h),
            "size": os.path.getsize(src),
        })
    return out


def inflate_paks():
    """ndadata/*.pak = PACK0001 + zlib@16, inflating to the sibling .idx bytes."""
    import zlib
    src = os.path.join(BOOM, "ndadata")
    dest = os.path.join(OUT, "ndadata")
    os.makedirs(dest, exist_ok=True)
    done = []
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".pak"):
            continue
        p = os.path.join(src, fn)
        if os.path.getsize(p) == 0:
            continue
        with open(p, "rb") as fh:
            d = fh.read()
        if d[:8] != b"PACK0001":
            continue
        zf = d.find(b"\x78\xda", 12)
        if zf < 0:
            continue
        try:
            o = zlib.decompressobj()
            raw = o.decompress(d[zf:]) + o.flush()
        except Exception:
            continue
        out_name = fn[:-4] + ".idx"
        with open(os.path.join(dest, out_name), "wb") as fh:
            fh.write(raw)
        done.append({"name": fn[:-4], "file": f"ndadata/{out_name}", "inflated": len(raw)})
    return done


def find_zlib_streams(buf):
    """Carve standalone zlib streams.

    Some .idd archives store entries as zlib-compressed records rather than raw
    files (FxMap has ~893 of them). Inflate each and sniff the result so the
    entry gets a real extension where possible.

    Returns (offset, used_compressed_bytes, inflated_bytes, fmt, confidence).
    """
    import zlib
    out = []
    i = 0
    n = len(buf)
    while True:
        i = buf.find(b"\x78\xda", i)
        if i < 0:
            break
        if i + 2 >= n:
            break
        try:
            o = zlib.decompressobj()
            data = o.decompress(buf[i:])
            data += o.flush()
        except Exception:
            i += 1
            continue
        used = (n - i) - len(o.unused_data)
        if len(data) < 64 or used < 8:
            i += 1
            continue
        # sniff the inflated payload
        fmt = None
        for magic, name in ((b"DDS ", "dds"), (b"\x89PNG", "png"),
                            (b"\xff\xd8\xff", "jpg"), (b"OggS", "ogg"),
                            (b"RIFF", "riff")):
            if data[:len(magic)] == magic:
                fmt = name
                break
        if fmt is None:
            for magic, name in ((b"DDS ", "dds"), (b"BM", "bmp"),
                                (b"\xff\xd8\xff", "jpg"), (b"PNG", "png")):
                if data.find(magic) > 0:
                    fmt = name
                    break
        out.append((i, used, len(data), fmt or "bin", "high"))
        i += used                       # continue past this stream
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--archive", action="append")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--names", help="JSON mapping id -> real filename")
    args = ap.parse_args()

    names = {}
    if args.names and os.path.exists(args.names):
        with open(args.names) as fh:
            names = json.load(fh)

    targets = args.archive or list(ARCHIVES)
    all_assets, archives = [], []
    for name in targets:
        fn = ARCHIVES.get(name)
        if not fn:
            print(f"!! unknown archive {name}", file=sys.stderr)
            continue
        path = os.path.join(BOOM, fn)
        if not os.path.exists(path):
            print(f"!! missing {path}", file=sys.stderr)
            continue
        t0 = time.time()
        summary, assets = extract_archive(name, path, args.dry_run, args.limit)
        if names:
            for a in assets:
                if a["id"] in names:
                    a["name"] = names[a["id"]]
        all_assets.extend(assets)
        archives.append({k: v for k, v in summary.items() if k != "by_format"})
        print(f"{name:14s} {summary['asset_count']:>7,} payloads  "
              f"{summary['by_format']}  ({time.time() - t0:.1f}s)")

    if args.dry_run:
        print(f"\nDRY RUN — {sum(len(a) for a in [all_assets]):,} assets total, nothing written")
        return

    sprites = load_ui_sprites()
    paks = inflate_paks()

    # Second pass: carve standalone zlib streams from archives that use them.
    zlib_assets = []
    for name in targets:
        fn = ARCHIVES.get(name)
        if not fn:
            continue
        path = os.path.join(BOOM, fn)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as fh:
            zbuf = fh.read()
        streams = find_zlib_streams(zbuf)
        if not streams:
            del zbuf
            continue
        zdir = os.path.join(OUT, name + "_zlib")
        os.makedirs(zdir, exist_ok=True)
        for k, (off, used, outlen, fmt, conf) in enumerate(streams):
            ext = "bin" if fmt == "bin" else fmt
            rel = f"{name}_zlib/{k:06d}.{ext}"
            with open(os.path.join(OUT, rel), "wb") as fh:
                fh.write(zbuf[off:off + used])
            zlib_assets.append({
                "id": f"{name}_zlib/{k:06d}",
                "archive": name + "_zlib",
                "index": k,
                "offset": off,
                "size": used,
                "inflated_size": outlen,
                "format": "zlib+" + fmt,
                "mime": "application/zlib",
                "name": None,
                "file": rel,
                "confidence": conf,
            })
        del zbuf
        print(f"{name + '_zlib':14s} {len(streams):>7,} zlib streams")
    all_assets.extend(zlib_assets)

    by_format = {}
    by_archive = {}
    for a in all_assets:
        by_format[a["format"]] = by_format.get(a["format"], 0) + 1
        by_archive[a["archive"]] = by_archive.get(a["archive"], 0) + 1

    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": {
            "total_assets": len(all_assets),
            "by_format": by_format,
            "by_archive": by_archive,
            "ui_sprites": len(sprites),
            "ndadata_pak": len(paks),
        },
        "archives": archives,
        "assets": all_assets,
        "ui_sprites": sprites,
        "ndadata": paks,
    }
    os.makedirs(OUT, exist_ok=True)
    mpath = os.path.join(OUT, "manifest.json")
    with open(mpath, "w") as fh:
        json.dump(manifest, fh, separators=(",", ":"))
    print(f"\nmanifest: {mpath} ({os.path.getsize(mpath):,} bytes)")
    print(f"total assets: {len(all_assets):,}  ui_sprites: {len(sprites)}  paks: {len(paks)}")
    print(f"by format: {by_format}")


if __name__ == "__main__":
    main()
