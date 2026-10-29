#!/usr/bin/env python3
"""Extract the ndadata bundles of the Club Audition client.

Model (all of this was derived from bytes and validated per file, not guessed):

    .idx  header:  u32 magic (fc 01 b2 05) | u32 version=15 | u32 countA | u32 countB
    .idx  records, from offset 12:
        u32 len | stem[len] | u32 A | u32 B | u32 C | u32 zero
      - stem  is the ciphered name; the cipher is already solved (see idx_decrypt)
        and is reused here, not re-derived.
      - B     is the STORED SIZE of the record's blob (see below).
      - C     is always 0.
      - A     is UNRESOLVED.  It does not match any of: a file offset into the
        .idd, the running sum of B, a CRC/FNV/Adler of the name or of the blob,
        the record's own position, nor the next/previous record's A.  It is
        reproducible from the .idx but its meaning is not known.  It is recorded
        in the manifest and no file placement depends on it.
    record 0 is a shorter form whose trailing C/zero fields are absent
    (u32 len | stem | u32 A | u32 B); i.e. strides differ for the first record.

    .idd  payloads are stored CONTIGUOUSLY, in record order, starting at byte 0,
    back to back, with no padding.  Proof: for the bundles where the .idx parses
    to completion the sum of every record's B equals the .idd size EXACTLY
    (e.g. MonWarsRank2nd 423990, 21thBirthPopUp 868279, EventPopup_* 4171585).
    So a record's byte offset is the running sum of the preceding B values.

Content forms actually observed and how each is validated:
  - `.luc`  : raw Lua 5.0 bytecode, starts 1b 4c 75 61 50.  Validated by header.
  - `.jpg`  : raw JPEG.  Validated by a full segment-chain walk that must end in
              an EOI at exactly the stored size.
  - `.bmp` / `.png` : NOT stored as bare images.  Every one begins with the same
              little-endian sprite descriptor (leading u32 in {1,5,6,10,...},
              then 2, 1, 0, then a width and a height at u32 16 and 20).  The
              payload region after the descriptor does not inflate with zlib at
              any window and does not contain a nested BM/PNG header, so the
              pixels are in an engine-private sprite encoding.  These are written
              out as `.spr` wrappers and marked confidence "low" — they are NOT
              presented as recovered BMP/PNG assets.
  - `.xml`  : stored raw, starts `<?xml`.  Validated by header.

Usage:
    python3 -I extract_ndadata.py [--out DIR] [--manifest FILE] [--limit N]
"""
import argparse
import glob
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOM = os.path.join(ROOT, "extracted", "Boom")
ND = os.path.join(BOOM, "ndadata")
OUT_DEFAULT = os.path.join(ROOT, "work", "assets_named", "ndadata")

MAGIC = b"\xfc\x01\xb2\x05"
IDD_MAGIC_CA = b"\xca\xda\xef"

# Directories the client uses at the head of a stored path.  This list is the
# only prior knowledge the name cipher needs; it is the same list as
# idx_decrypt.py.
DIRS = ("Quest/", "PopupEvent/", "Game/", "Item/", "Icon/", "Event/", "Data/",
        "Popup/", "Interface/", "Img/", "Sound/", "Effect/", "Back/", "Ui/",
        "UI/", "Monster/", "Object/", "Path/", "Cash/", "Pet/", "Npc/",
        "Stage/", "Map/", "Texture/", "Image/", "Model/", "Anim/", "Font/",
        "Music/", "Voice/", "Bgm/", "Loading/", "Common/", "Character/",
        "Avatar/", "Movie/", "Wave/", "see/", "Disp/", "Item2/")
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".luc", ".xml", ".dds", ".tga",
        ".txt", ".dat", ".ini", ".wav", ".ogg", ".ani", ".fft", ".cur",
        ".ico", ".bik", ".slk", ".scr", ".wdb", ".lua")


def decrypt(stem, seed):
    """name[i] = stem[i] ^ name[i-4]; the head is seeded by a 4-byte IV."""
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def try_name(stem):
    """Recover a stored path, seeding from each known directory prefix.

    Deterministic: a candidate is accepted only when the seed implied by a
    prefix yields a path that really starts with that prefix and ends in a
    known extension.  No scoring, so no false accepts from printable garbage.
    """
    if len(stem) < 4:
        return None
    for pfx in DIRS:
        pb = pfx.encode()
        if len(pb) < 4 or len(stem) < len(pb):
            continue
        seed = bytes(stem[i] ^ pb[i] for i in range(4))
        nm = decrypt(stem, seed)
        if not nm.startswith(pb):
            continue
        if any(b < 31 or b > 126 for b in nm):
            continue
        s = nm.rstrip(b"\x00").decode("latin1")
        if s.lower().endswith(EXTS) and "//" not in s and "/." not in s:
            return s
    return None


def parse_idx(path):
    """Return (idx_bytes, [(recpos, stemlen, name, A, B, C, zero), ...]).

    Record 0 is the short form and is located by finding the first regular
    record; every later record is stepped with the regular stride
    4 + len + 16.  Returns None for the record list when the walk does not
    consume the whole file.
    """
    with open(path, "rb") as fh:
        d = fh.read()
    if d[:4] != MAGIC or len(d) < 24:
        return d, None

    # locate the first regular record: the earliest position whose name is valid
    # and whose successor is also a valid record (or which ends the file)
    first = None
    for p in range(16, len(d) - 20):
        ln = struct.unpack_from("<I", d, p)[0]
        if not (4 < ln < 2048 and p + 4 + ln + 16 <= len(d)):
            continue
        if try_name(d[p + 4:p + 4 + ln]) is None:
            continue
        nxt = p + 4 + ln + 16
        if nxt == len(d):
            first = p
            break
        if nxt + 4 <= len(d):
            ln2 = struct.unpack_from("<I", d, nxt)[0]
            if 4 < ln2 < 2048 and nxt + 4 + ln2 + 16 <= len(d) \
                    and try_name(d[nxt + 4:nxt + 4 + ln2]) is not None:
                first = p
                break
    if first is None:
        return d, None

    recs = []
    # short form record 0: u32 len | stem | u32 A | u32 B
    if first - 12 > 16:
        stem0 = d[16:first - 12]
        nm0 = try_name(stem0)
        if nm0 is not None:
            A, B = struct.unpack_from("<II", d[first - 8])
            recs.append((16, len(stem0), nm0, A, B, 0, 0))
    p = first
    while p + 4 <= len(d):
        ln = struct.unpack_from("<I", d, p)[0]
        if not (4 < ln < 2048 and p + 4 + ln + 16 <= len(d)):
            break
        nm = try_name(d[p + 4:p + 4 + ln])
        if nm is None:
            break
        A, B, C, Z = struct.unpack_from("<IIII", d, p + 4 + ln)
        recs.append((p, ln, nm, A, B, C, Z))
        p = p + 4 + ln + 16
    complete = (p == len(d))
    return d, (recs, complete)


# ---------------------------------------------------------------- validators

def valid_lua(p):
    return p[:4] == b"\x1bLua" or p[:5] == b"\x1bLuaP"


def valid_jpeg(p):
    """Full segment-chain walk; returns the extent ending at EOI, or None."""
    if p[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 4 <= len(p):
        if p[i] != 0xFF:
            return None
        m = p[i + 1]
        if m == 0xD8:
            i += 2
            continue
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        if m == 0xD9:
            return i + 2
        ln = struct.unpack_from(">H", p, i + 2)[0]
        if ln < 2:
            return None
        if m == 0xDA:
            j = i + 2 + ln
            while j + 1 < len(p):
                if p[j] == 0xFF and p[j + 1] == 0xD9:
                    return j + 2
                j += 1
            return None
        i = i + 2 + ln
    return None


def valid_bmp(p):
    if p[:2] != b"BM" or len(p) < 54:
        return None
    sz = struct.unpack_from("<I", p, 2)[0]
    if 54 <= sz <= len(p):
        return sz
    return None


def valid_png(p):
    if p[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    j = p.find(b"IEND")
    return j + 8 if j >= 0 else None


def valid_xml(p):
    return p[:5] == b"<?xml"


def valid_riff(p):
    if p[:4] != b"RIFF" or len(p) < 12:
        return None
    sz = struct.unpack_from("<I", p, 4)[0]
    return sz + 8 if 12 <= sz + 8 <= len(p) else None


def valid_dds(p):
    return p[:4] == b"DDS "


def classify(blob):
    """Return (kind, confidence, detail, extent).

    kind is the TRUE format of the stored bytes, which is not always the
    extension the name claims.  Only a format that parses from its own header
    is reported as that format.
    """
    if valid_lua(blob):
        return "lua", "high", "Lua 5.0 bytecode header", 5
    if valid_xml(blob):
        return "xml", "high", "xml declaration", 5
    e = valid_jpeg(blob)
    if e is not None:
        if e == len(blob):
            return "jpeg", "high", "segment chain ends at EOI == stored size", e
        return "jpeg", "low", f"EOI at {e} but stored size {len(blob)}", e
    b = valid_bmp(blob)
    if b is not None:
        return "bmp", ("high" if b == len(blob) else "low"), \
            f"bfSize={b} stored={len(blob)}", b
    pn = valid_png(blob)
    if pn is not None:
        return "png", ("high" if pn == len(blob) else "low"), \
            f"IEND at {pn} stored={len(blob)}", pn
    r = valid_riff(blob)
    if r is not None:
        return "riff", "high", f"RIFF size {r}", r
    if valid_dds(blob):
        return "dds", "high", "DDS fourcc", 4
    return "sprite", "low", "engine sprite descriptor, not a bare image", 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--manifest",
                    default=os.path.join(OUT_DEFAULT, "manifest.json"))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    entries = []
    bundle_rows = []

    idx_paths = sorted(glob.glob(os.path.join(ND, "*.idx")))
    for ip in idx_paths:
        name = os.path.basename(ip)[:-4]
        iddp = os.path.join(ND, name + ".idd")
        d, parsed = parse_idx(ip)
        if parsed is None or not parsed[0]:
            bundle_rows.append({
                "bundle": name, "records": 0, "extracted": 0,
                "idd_size": os.path.getsize(iddp) if os.path.exists(iddp) else 0,
                "bytes_covered": 0, "coverage": 0.0, "note": "no parseable records",
            })
            continue
        recs, complete = parsed
        idd = open(iddp, "rb").read() if os.path.exists(iddp) else b""
        idd_size = len(idd)

        off = 0
        n_ok = 0
        n_low = 0
        covered = 0
        for rpos, slen, nm, A, B, C, Z in recs:
            blob = idd[off:off + B]
            kind, conf, detail, _ext = classify(blob)
            ext = nm.rsplit(".", 1)[-1].lower()
            # store with an extension that reflects the true content
            store_ext = {"jpeg": "jpg", "lua": "luc", "sprite": ext}.get(kind, kind)
            rel = os.path.join(name, nm.replace("/", os.sep) + "." + store_ext)
            dest = os.path.join(args.out, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(blob)
            entries.append({
                "bundle": name,
                "bundle_rel": os.path.relpath(dest, args.out),
                "name": nm,
                "record_pos": rpos,
                "stem_len": slen,
                "offset": off,
                "size": B,
                "idx_field_A": A,
                "idx_field_B_size": B,
                "idx_field_C": C,
                "stored_ext": ext,
                "detected_format": kind,
                "detected_detail": detail,
                "file": rel,
                "confidence": conf,
            })
            if conf == "high":
                n_ok += 1
            else:
                n_low += 1
            covered += len(blob)
            off += B

        cov = covered / idd_size if idd_size else 0.0
        # coverage is measured against the bytes actually taken, and the true
        # check is whether the packed records tile the .idd exactly
        bundle_rows.append({
            "bundle": name,
            "records": len(recs),
            "idx_complete": complete,
            "sum_stored_size": sum(r[4] for r in recs),
            "idd_size": idd_size,
            "bytes_written": covered,
            "coverage": round(cov, 6),
            "tiles_idd_exactly": covered == idd_size,
            "validated_high": n_ok,
            "low_confidence": n_low,
        })
        print(f"{name:34s} recs={len(recs):3d} write={covered:9d} "
              f"idd={idd_size:9d} cov={cov*100:6.2f}% "
              f"exact={covered == idd_size} high={n_ok} low={n_low}")
        # write partial results as we go, so a crash never loses everything
        with open(args.manifest, "w") as fh:
            json.dump({"bundles": bundle_rows, "entries": entries}, fh, indent=1)

    # aggregate
    tot_rec = sum(b["records"] for b in bundle_rows)
    tot_high = sum(b.get("validated_high", 0) for b in bundle_rows)
    tot_low = sum(b.get("low_confidence", 0) for b in bundle_rows)
    exact = [b["bundle"] for b in bundle_rows if b.get("tiles_idd_exactly")]
    partial = [b["bundle"] for b in bundle_rows if not b.get("tiles_idd_exactly")
               and b["records"]]
    summary = {
        "bundles": len(bundle_rows),
        "records_total": tot_rec,
        "validated_high": tot_high,
        "low_confidence": tot_low,
        "pass_rate": round(tot_high / tot_rec, 4) if tot_rec else 0.0,
        "bundles_tiling_idd_exactly": exact,
        "bundles_incomplete": partial,
        "field_A": "UNRESOLVED",
        "field_B": "stored size in bytes",
        "payload_base_offset": 0,
    }
    with open(args.manifest, "w") as fh:
        json.dump({"summary": summary, "bundles": bundle_rows,
                   "entries": entries}, fh, indent=1)

    print()
    print(f"bundles        : {len(bundle_rows)}")
    print(f"records        : {tot_rec}")
    print(f"high confidence: {tot_high}")
    print(f"low confidence : {tot_low}")
    print(f"pass rate      : {summary['pass_rate']*100:.1f}%")
    print(f"tile .idd      : {len(exact)} bundles exactly")
    print(f"wrote          : {args.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
