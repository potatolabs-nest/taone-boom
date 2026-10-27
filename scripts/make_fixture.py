#!/usr/bin/env python3
"""Carve a small synthetic fixture tree for the app from the real game archives.

Writes app/public/{Fixtures*,vh,ndadata,ssidata} plus app/public/manifest.json.
This produces a FIXTURE manifest matching the real schema, for developing the app
before the real extractor finishes. Not part of the app itself.

Run:  python3 -I scripts/make_fixture.py
"""
import json
import os
import shutil
import struct
import sys
import time
import zlib

ROOT = "/Users/hieu/Workspaces/taone"
SRC = os.path.join(ROOT, "extracted", "Boom")
PUB = os.environ.get("FIXTURE_OUT") or os.path.join(ROOT, "app", "public")
SSI = os.path.join(ROOT, "work", "ssi")


def ogg_len(d, off):
    """Walk Ogg pages from a page start; return total byte length or None."""
    total = 0
    p = off
    while True:
        if d[p:p + 4] != b"OggS":
            return None
        flags = d[p + 5]
        nseg = d[p + 26]
        seg = d[p + 27:p + 27 + nseg]
        if len(seg) < nseg:
            return None
        total += 27 + nseg + sum(seg)
        p = off + total
        if flags & 0x04:               # EOS page terminates the logical stream
            return total
        if total > 8_000_000:
            return None


def carve(path, magic, count, length_fn, cap=16_000_000):
    d = open(path, "rb").read(cap)
    out = []
    pos = 0
    while len(out) < count:
        i = d.find(magic, pos)
        if i < 0:
            break
        n = length_fn(d, i)
        pos = i + 4
        if not n or n < 32 or i + n > len(d):
            continue
        out.append((i, d[i:i + n]))
        pos = i + n
    return out


def bmp_len(d, off):
    if off + 30 > len(d):
        return None
    size = struct.unpack_from("<I", d, off + 2)[0]
    if size < 54 or size > 4_000_000 or d[off + 14:off + 16] not in (b"\x28\x00", b"\x0c\x00"):
        return None
    return size


def png_len(d, off):
    e = d.find(b"IEND", off)
    return (e + 8) - off if e > 0 else None


def dds_len(d, off):
    if off + 128 > len(d):
        return None
    h = struct.unpack_from("<I", d, off + 4)[0]
    if h != 124:
        return None
    mips = struct.unpack_from("<I", d, off + 28)[0] or 1
    w = struct.unpack_from("<I", d, off + 16)[0]
    hh = struct.unpack_from("<I", d, off + 12)[0]
    fourcc = d[off + 84:off + 88]
    bpb = 16 if fourcc in (b"DXT1", b"DXT4") else (8 if fourcc == b"ATI1" else 16)
    total = 128
    for lvl in range(max(1, min(mips, 16))):
        ww, hhh = max(1, w >> lvl), max(1, hh >> lvl)
        total += max(1, (ww + 3) // 4) * max(1, (hhh + 3) // 4) * bpb
    return total if total <= len(d) - off else None


def synth_png(w, h, rgb):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


DDS_COLORS = [(220, 60, 60), (60, 200, 120), (70, 120, 240), (230, 180, 40),
              (170, 90, 220), (60, 200, 220)]


def _rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def dds_dxt1(w, h, rgb):
    """A valid single-mip 64-bit-per-4x4-block DXT1 DDS of one solid colour."""
    bw, bh = max(1, (w + 3) // 4), max(1, (h + 3) // 4)
    data_size = bw * bh * 8
    c = _rgb565(*rgb)
    block = struct.pack("<HHI", c, 0, 0)          # colour0, colour1, all index 0
    hdr = bytearray(128)
    hdr[0:4] = b"DDS "
    struct.pack_into("<I", hdr, 4, 124)           # dwSize
    struct.pack_into("<I", hdr, 8, 0x81007)       # CAPS|HEIGHT|WIDTH|PIXELFORMAT|LINEARSIZE
    struct.pack_into("<I", hdr, 12, h)            # dwHeight
    struct.pack_into("<I", hdr, 16, w)            # dwWidth
    struct.pack_into("<I", hdr, 20, data_size)    # dwPitchOrLinearSize
    struct.pack_into("<I", hdr, 28, 1)            # dwMipMapCount
    struct.pack_into("<I", hdr, 76, 32)           # DDS_PIXELFORMAT.dwSize
    struct.pack_into("<I", hdr, 80, 0x4)          # DDPF_FOURCC
    hdr[84:88] = b"DXT1"                          # dwFourCC
    struct.pack_into("<I", hdr, 108, 0x1000)      # dwCaps = DDSCAPS_TEXTURE
    return bytes(hdr) + block * (bw * bh)


def main():
    if not os.path.isdir(PUB):
        os.makedirs(PUB)
    assets_root = os.path.join(PUB, "fixture-assets")
    if os.path.isdir(assets_root):
        shutil.rmtree(assets_root)
    for sub in ("FixtureSound", "FixtureImg", "FixtureTex", "FixturePNG", "vh", "ndadata", "ssidata"):
        os.makedirs(os.path.join(PUB, sub), exist_ok=True)

    assets = []
    archives = {}

    def add(archive, idx, blob, fmt, mime, name=None, conf="high"):
        rel = "%s/%06d.%s" % (archive, idx, fmt)
        dst = os.path.join(PUB, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(blob)
        assets.append({"id": "%s/%06d" % (archive, idx), "archive": archive, "index": idx,
                       "offset": 0, "size": len(blob), "format": fmt, "mime": mime,
                       "name": name, "file": rel, "confidence": conf})
        a = archives.setdefault(archive, {"name": archive, "idd_size": 0, "asset_count": 0})
        a["asset_count"] += 1

    # --- real carved Ogg Vorbis from FxSound.idd -------------------------
    oggs = carve(os.path.join(SRC, "FxSound.idd"), b"OggS", 14, ogg_len)
    for n, (off, blob) in enumerate(oggs):
        add("FxSound", n, blob, "ogg", "audio/ogg", None, "high")
    # a few name-bearing audio entries (names in the real manifest come from .idx)
    for n, (off, blob) in enumerate(oggs[:6]):
        add("FxSound", 1000 + n, blob, "ogg", "audio/ogg",
            ["BGM_Lobby", "FX_Click", "FX_Combo01", "FX_Applause", "FX_GameStart", "VO_Ready"][n], "medium")

    # --- real vh/*.bmp reused as image assets (archive "vh") -----------
    vh_dir = os.path.join(SRC, "vh")
    vh_files = sorted(f for f in os.listdir(vh_dir) if f.lower().endswith(".bmp"))
    for n, fn in enumerate(vh_files[:8]):
        blob = open(os.path.join(vh_dir, fn), "rb").read()
        with open(os.path.join(PUB, "vh", fn), "wb") as f:
            f.write(blob)
        add("vh", n, blob, "bmp", "image/bmp", os.path.splitext(fn)[0], "high")

    # --- synthetic DDS (DXT1) placeholders ------------------------------
    # Proper 128-byte DDS_HEADER: DDS_PIXELFORMAT starts at 76, its dwFourCC
    # at 84. Each file is a 64x64 DXT1 image of one solid colour (16x16
    # blocks, all colour indices 0 -> colour0).
    for n in range(6):
        add("fx", n, dds_dxt1(64, 64, DDS_COLORS[n % len(DDS_COLORS)]), "dds",
            "image/vnd-ms.dds", "tex_%02d" % n, "low")

    # --- synthetic PNGs (several sizes, incl. wide sprite-like) ---------
    png_specs = [(64, 48, (40, 90, 200)), (128, 96, (200, 60, 90)), (48, 48, (60, 170, 90)),
                 (256, 64, (150, 80, 190)), (92, 36, (220, 160, 40))]
    for n, (w, h, c) in enumerate(png_specs):
        add("FixturePNG", n, synth_png(w, h, c), "png", "image/png", "gen_%dx%d" % (w, h), "high")

    # --- ui_sprites from the real, plaintext vh/*.bmp --------------------
    ui = []
    vh = os.path.join(SRC, "vh")
    for fn in sorted(os.listdir(vh)):
        if not fn.lower().endswith(".bmp"):
            continue
        blob = open(os.path.join(vh, fn), "rb").read()
        w, h = struct.unpack_from("<ii", blob, 18)
        dst = os.path.join(PUB, "vh", fn)
        with open(dst, "wb") as f:
            f.write(blob)
        ui.append({"name": os.path.splitext(fn)[0], "file": "vh/" + fn,
                   "width": w, "height": abs(h), "size": len(blob)})

    # --- ndadata: real inflated .pak sizes ------------------------------
    nda = []
    nd = os.path.join(SRC, "ndadata")
    os.makedirs(os.path.join(PUB, "ndadata"), exist_ok=True)
    for fn in sorted(os.listdir(nd)):
        if not fn.endswith(".pak"):
            continue
        blob = open(os.path.join(nd, fn), "rb").read()
        base = fn[:-4]
        inflated = 0
        if blob[8:16] == b"" or blob[:8] == b"PACK0001":
            try:
                inflated = len(zlib.decompress(blob[16:]))
            except Exception:
                inflated = 0
        sidx = os.path.join(nd, base + ".idx")
        if not inflated and os.path.exists(sidx):
            inflated = os.path.getsize(sidx)
        with open(os.path.join(PUB, "ndadata", base + ".idx"), "wb") as f:
            f.write(blob)
        nda.append({"name": base, "file": "ndadata/%s.idx" % base, "inflated": inflated})
        if len(nda) >= 12:
            break

    # --- ssidata: real decoded strings + CP949 source blobs --------------
    # .strings.txt are the ASCII-only decoded lines (strings >=5 chars).
    # .bin blobs (.ssd/.ini) hold the REAL CP949 Korean; the app decodes those
    # with TextDecoder('euc-kr') so Korean renders correctly.
    nfiles = 0
    ssd_out = os.path.join(PUB, "ssidata")
    for fn in sorted(os.listdir(SSI)):
        if not (fn.endswith(".strings.txt") or fn.endswith(".bin")):
            continue
        src = os.path.join(SSI, fn)
        shutil.copy2(src, os.path.join(ssd_out, fn))
        nfiles += 1
    index = []
    for fn in sorted(os.listdir(ssd_out)):
        if fn == "index.json":
            continue
        src = os.path.join(ssd_out, fn)
        bytes_ = os.path.getsize(src)
        index.append({"name": fn, "bytes": bytes_,
                      "encoding": "euc-kr" if fn.endswith(".bin") else "utf-8"})
    with open(os.path.join(ssd_out, "index.json"), "w") as f:
        json.dump({"files": index}, f, indent=1)
    nfiles = len(index)

    by_fmt, by_arc = {}, {}
    for a in assets:
        by_fmt[a["format"]] = by_fmt.get(a["format"], 0) + 1
        by_arc[a["archive"]] = by_arc.get(a["archive"], 0) + 1

    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fixture": True,
        "summary": {"total_assets": len(assets), "by_format": by_fmt, "by_archive": by_arc,
                    "ui_sprites": len(ui), "ndadata_pak": len(nda)},
        "archives": sorted(archives.values(), key=lambda x: x["name"]),
        "assets": assets,
        "ui_sprites": ui,
        "ndadata": nda,
    }
    with open(os.path.join(PUB, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print("assets=%d ui_sprites=%d ndadata=%d ssidata=%d"
          % (len(assets), len(ui), len(nda), nfiles))
    print("formats:", by_fmt)


if __name__ == "__main__":
    sys.exit(main())
