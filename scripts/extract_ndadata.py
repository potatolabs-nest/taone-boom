#!/usr/bin/env python3
"""Extract the ndadata bundles of the Club Audition client.

Everything below was derived from the bytes and is validated per file.  The
name cipher itself was already solved (see idx_decrypt.py) and is reused here,
not re-derived.

.idx layout
-----------
    header :  u32 magic (fc 01 b2 05) | u32 version=15 | u32 countA | u32 countB

    record :  u32 len | stem[len] | u32 A | u32 size | u32 zero
              (regular records; stride 4 + len + 16)

    record 0 uses the short form - a 12-byte trailer (A, size, 0) instead of 16 -
    and its stored `len` field is not the stem length, so record 0's stem is
    taken as everything between offset 16 and the first regular record (or EOF)
    minus that 12-byte trailer.  This is why a naive `[u32 len][name]` walk fails
    on the first record.

    `stem` is the ciphered name; `size` is the record's stored byte count;
    `zero` is always 0.

    Field A is UNRESOLVED.  It is not a file offset into the .idd, not the
    running sum of `size`, not a CRC32 / Adler32 / FNV-1a / djb2 of the name,
    the stem or the blob, and not the record's own or its neighbours' position.
    It is recorded in the manifest; no file placement depends on it.

.idd layout
-----------
    Payloads are stored CONTIGUOUSLY in record order from byte 0, back to back,
    with no padding and no index header.  Proof: the sum of every record's
    `size` equals the .idd size EXACTLY for all 29 name-bearing bundles
    (e.g. MonWarsRank2nd 423990, 21thBirthPopUp 868279,
    EventPopup_CABoard_* 4171585) and for the single-record Icon bundles
    (e.g. IconBingGo01 2921).  A record's byte offset is therefore the running
    sum of the preceding sizes.

Content validation (a magic hit is NOT an asset - each file is parsed)
--------------------------------------------------------------------
    .luc / .lua : raw Lua 5.0 bytecode, starts 1b 4c 75 61 50  -> "high"
    .jpg        : raw JPEG; a full segment-chain walk must end in EOI at
                  exactly the stored size                          -> "high"
    .xml        : stored raw, starts `<?xml`                      -> "high"
    .bmp / .png : NOT stored as bare images.  Every one begins with an
                  engine sprite descriptor (leading u32 in {1,2,4,5,6,10,...},
                  then 2, 1, 0, then width and height).  The body after the
                  descriptor does not inflate with zlib at any window and holds
                  no nested BM/PNG header, so the pixels are in an engine-private
                  sprite encoding.  Written out under the name's own extension
                  and marked "low"; they are NOT presented as recovered images.

Usage:
    python3 -I extract_ndadata.py [--out DIR] [--manifest FILE]
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

# Directory prefixes the client uses.  Only prior knowledge the name cipher
# needs; same set as idx_decrypt.py plus Icon/ and Item/ for the small bundles.
DIRS = ("Quest/", "PopupEvent/", "Game/", "Item/", "Icon/", "Event/", "Data/",
        "Popup/", "Interface/", "Img/", "Sound/", "Effect/", "Back/", "Ui/",
        "UI/", "Monster/", "Object/", "Path/", "Cash/", "Pet/", "Npc/",
        "Stage/", "Map/", "Texture/", "Image/", "Model/", "Anim/", "Font/",
        "Music/", "Voice/", "Bgm/", "Loading/", "Common/", "Character/",
        "Avatar/", "Movie/", "Wave/", "see/", "Disp/", "Item2/", "ShopTop/")
# Extensions plus the suffixless leaf names the Icon bundles use
# (Icon/BingGo01, Icon/Bomb585icon, Icon/A02_10_3006icon, ...).
EXTS = (".bmp", ".jpg", ".jpeg", ".png", ".luc", ".xml", ".dds", ".tga",
        ".txt", ".dat", ".ini", ".wav", ".ogg", ".ani", ".fft", ".cur",
        ".ico", ".bik", ".slk", ".scr", ".wdb", ".lua", "icon", "item",
        "img", "bt", "bg")


def decrypt(stem, seed):
    """name[i] = stem[i] ^ name[i-4]; the head is seeded by a 4-byte IV."""
    out = bytearray(len(stem))
    for i in range(len(stem)):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def try_name(stem, bundle=None):
    """Recover a stored path, deriving the seed from each known directory.

    Deterministic: a candidate is accepted only when the seed implied by a
    prefix yields a path that really starts with that prefix and ends in a
    known extension.  No scoring, so no false accepts from printable garbage.

    The small Icon bundles store a leaf with no extension ("Icon/BingGo01").
    Those are accepted only when the leaf also appears in the bundle filename,
    which keeps the ambiguous seeds from accepting plain garbage.
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
        if "//" in s or "/." in s or s.endswith("/"):
            continue
        if s.lower().endswith(EXTS):
            return s
        # extensionless leaf: accept only if it echoes the bundle name
        if bundle:
            leaf = s.rsplit("/", 1)[-1]
            if len(leaf) >= 4 and leaf.lower() in bundle.lower():
                return s
    return None


def parse_idx(path, bundle=None):
    """Return (idx_bytes, [(recpos, stemlen, name, A, size, C), ...], complete).

    Returns records=None when the .idx does not walk cleanly.
    """
    with open(path, "rb") as fh:
        d = fh.read()
    n = len(d)
    if d[:4] != MAGIC or n < 40:
        return d, None, False

    # --- locate the first REGULAR record -----------------------------------
    # It is the earliest position whose name decrypts and whose successor is a
    # valid record (or which lands exactly at EOF).
    first = None
    for p in range(16, n - 20):
        ln = struct.unpack_from("<I", d, p)[0]
        if not (4 < ln < 2048 and p + 4 + ln + 16 <= n):
            continue
        if try_name(d[p + 4:p + 4 + ln], bundle) is None:
            continue
        nxt = p + 4 + ln + 16
        if nxt == n:
            first = p
            break
        if nxt + 4 <= n:
            ln2 = struct.unpack_from("<I", d, nxt)[0]
            if 4 < ln2 < 2048 and nxt + 4 + ln2 + 16 <= n \
                    and try_name(d[nxt + 4:nxt + 4 + ln2], bundle) is not None:
                first = p
                break

    recs = []
    if first is not None:
        # record 0 has the same 16-byte trailer as the rest but no u32 length
        # prefix, so its stem runs from offset 16 up to the trailer.
        L0 = first - 16 - 16
        if L0 >= 4:
            nm0 = try_name(d[16:16 + L0], bundle)
            if nm0 is not None:
                _h, A, size, _z = struct.unpack_from("<IIII", d, first - 16)
                recs.append((16, L0, nm0, A, size, 0))
        p = first
        while p + 4 <= n:
            ln = struct.unpack_from("<I", d, p)[0]
            if not (4 < ln < 2048 and p + 4 + ln + 16 <= n):
                break
            nm = try_name(d[p + 4:p + 4 + ln], bundle)
            if nm is None:
                break
            f0, A, size, Z = struct.unpack_from("<IIII", d, p + 4 + ln)
            recs.append((p, ln, nm, A, size, f0))
            p = p + 4 + ln + 16
        if recs and p == n:
            return d, recs, True
        # fall through to single-record handling if that did not complete

    # --- single-record bundles (icon sets) ---------------------------------
    # layout identical to record 0 of the multi-record bundles:
    #     u32 len | stem[len] | u32 hash | u32 size | u32 zero
    # (the leading len here IS the stem length, unlike record 0 above).
    ln0 = struct.unpack_from("<I", d, 12)[0]
    if 4 < ln0 < 2048 and 16 + ln0 + 16 == n:
        nm0 = try_name(d[16:16 + ln0], bundle)
        if nm0 is not None:
            _h, A, size, _z = struct.unpack_from("<IIII", d, 16 + ln0)
            return d, [(12, ln0, nm0, A, size, 0)], True
    # last resort: stem runs from 16 to EOF minus the 16-byte trailer
    L0 = n - 16 - 16
    if L0 >= 4:
        nm0 = try_name(d[16:16 + L0], bundle)
        if nm0 is not None:
            _h, A, size, _z = struct.unpack_from("<IIII", d, n - 16)
            return d, [(16, L0, nm0, A, size, 0)], True
    return d, (recs or None), False


# ---------------------------------------------------------------- validators

def valid_lua(p):
    return p[:5] == b"\x1bLuaP" or p[:4] == b"\x1bLua"


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
    return sz if 54 <= sz <= len(p) else None


def valid_png(p):
    if p[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    j = p.find(b"IEND")
    return j + 8 if j >= 0 else None


def valid_lua_source(blob):
    """Lua 5.x source text (not compiled): mostly printable, with Lua tokens.

    The sources are CP949-encoded (Korean comments), so bytes >= 0x80 are
    allowed; the test is that the text has almost no control bytes and does
    contain Lua punctuation/keywords.
    """
    if not blob or blob[:1] == b"\x1b":
        return False
    sample = blob[:4096]
    ctrl = sum(1 for b in sample if b < 9 or (13 < b < 32) or b == 127)
    if ctrl > len(sample) * 0.02:
        return False
    return any(tok in blob for tok in (b"--", b"function", b"local", b"return", b"="))


def validate(blob, ext):
    """Return (format, confidence, detail).

    `format` is the TRUE format parsed from the bytes, which is not always what
    the name claims.  A bare BMP/PNG would be reported as such with "high"; in
    practice none is stored bare, so those come back as "sprite"/"low".
    """
    if valid_lua(blob):
        return "lua_bytecode", "high", "Lua 5.0 bytecode header"
    if ext in ("lua", "luc") and valid_lua_source(blob):
        return "lua_source", "high", "Lua source text"
    if blob[:5] == b"<?xml":
        return "xml", "high", "xml declaration"
    e = valid_jpeg(blob)
    if e is not None:
        if e == len(blob):
            return "jpeg", "high", "segment chain ends at EOI == stored size"
        return "jpeg", "low", f"EOI at {e}, stored {len(blob)}"
    b = valid_bmp(blob)
    if b is not None and b == len(blob):
        return "bmp", "high", f"bfSize {b} == stored size"
    pn = valid_png(blob)
    if pn is not None and pn == len(blob):
        return "png", "high", f"IEND at {pn} == stored size"
    if blob[:4] == b"DDS ":
        return "dds", "high", "DDS fourcc"
    if blob[:4] == b"RIFF" and len(blob) >= 12:
        sz = struct.unpack_from("<I", blob, 4)[0]
        if sz + 8 <= len(blob):
            return "riff", "high", f"RIFF size {sz + 8}"
    # engine sprite wrapper: <u32 kind><u32 2><u32 nframes>
    if len(blob) >= 24:
        u = struct.unpack_from("<III", blob, 0)
        if u[1] == 2 and 1 <= u[2] <= 16 and u[0] < 64:
            return "sprite", "low", \
                f"engine sprite descriptor (kind={u[0]}, frames={u[2]}); " \
                "not a bare image"
    return "unknown", "low", "no recognised header"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--manifest",
                    default=os.path.join(OUT_DEFAULT, "manifest.json"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    entries = []
    bundle_rows = []
    for ip in sorted(glob.glob(os.path.join(ND, "*.idx"))):
        name = os.path.basename(ip)[:-4]
        iddp = os.path.join(ND, name + ".idd")
        if not os.path.exists(iddp):
            continue
        d, recs, complete = parse_idx(ip, name)
        idd = open(iddp, "rb").read()
        if not recs:
            bundle_rows.append({
                "bundle": name, "records": 0, "extracted": 0,
                "idd_size": len(idd), "bytes_written": 0, "coverage": 0.0,
                "tiles_idd_exactly": False, "validated_high": 0,
                "low_confidence": 0, "note": "no parseable records",
            })
            continue

        off = 0
        n_high = n_low = 0
        for rpos, slen, nm, A, size, C in recs:
            blob = idd[off:off + size]
            leaf = nm.rsplit("/", 1)[-1]
            ext = leaf.rsplit(".", 1)[-1].lower() if "." in leaf else ""
            fmt, conf, detail = validate(blob, ext)
            # The output file keeps the client's own path and extension exactly;
            # the real byte format is recorded in the manifest.  Never append a
            # second extension - a stored `.luc` is Lua bytecode, and the client
            # itself relies on that name.
            rel = os.path.join(name, nm.replace("/", os.sep))
            dest = os.path.join(args.out, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(blob)
            entries.append({
                "bundle": name, "name": nm, "file": rel,
                "record_pos": rpos, "stem_len": slen, "offset": off,
                "size": size,
                "idx_field_A": A, "idx_field_size": size, "idx_field_C": C,
                "claimed_ext": ext, "detected_format": fmt,
                "detected_detail": detail, "confidence": conf,
            })
            if conf == "high":
                n_high += 1
            else:
                n_low += 1
            off += size

        exact = off == len(idd)
        bundle_rows.append({
            "bundle": name, "records": len(recs), "extracted": len(recs),
            "idx_complete": complete,
            "sum_size": sum(r[4] for r in recs), "idd_size": len(idd),
            "bytes_written": off, "coverage": round(off / len(idd), 6),
            "tiles_idd_exactly": exact,
            "validated_high": n_high, "low_confidence": n_low,
        })
        print(f"{name:34s} recs={len(recs):3d} write={off:9d} idd={len(idd):9d} "
              f"cov={off/len(idd)*100:6.2f}% exact={str(exact):5s} "
              f"high={n_high} low={n_low}")
        # persist partial results as we go
        with open(args.manifest, "w") as fh:
            json.dump({"bundles": bundle_rows, "entries": entries}, fh, indent=1)

    tot = sum(b["records"] for b in bundle_rows)
    hi = sum(b["validated_high"] for b in bundle_rows)
    lo = sum(b["low_confidence"] for b in bundle_rows)
    exact = [b["bundle"] for b in bundle_rows if b["tiles_idd_exactly"]]
    notexact = [b["bundle"] for b in bundle_rows
                if not b["tiles_idd_exactly"] and b["records"]]
    failed = [b["bundle"] for b in bundle_rows if not b["records"]]
    summary = {
        "bundles": len(bundle_rows),
        "records_total": tot,
        "validated_high": hi,
        "low_confidence": lo,
        "validation_pass_rate": round(hi / tot, 4) if tot else 0.0,
        "bundles_tiling_idd_exactly": exact,
        "bundles_not_tiling": notexact,
        "bundles_unparsed": failed,
        "field_A": "UNRESOLVED - see module docstring",
        "field_B": "stored size in bytes (sum equals .idd size exactly)",
        "payload_base_offset": 0,
    }
    with open(args.manifest, "w") as fh:
        json.dump({"summary": summary, "bundles": bundle_rows,
                   "entries": entries}, fh, indent=1)

    print()
    print(f"bundles          : {len(bundle_rows)}")
    print(f"records          : {tot}")
    print(f"validated high   : {hi}")
    print(f"low confidence   : {lo}")
    print(f"validation pass  : {summary['validation_pass_rate']*100:.1f}%")
    print(f"tile .idd exactly: {len(exact)} bundles")
    if notexact:
        print(f"NOT tiling       : {notexact}")
    if failed:
        print(f"UNPARSED         : {failed}")
    print(f"wrote            : {args.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
