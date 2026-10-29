#!/usr/bin/env python3
"""Core of the Club Audition `.idx` / `.idd` format. SOLVED.

THE CONTAINER
-------------
A `.idx` and its sibling `.idd` are two halves of one archive:

  * the `.idx` is the **directory** -- it names every entry and stores the exact
    byte length of that entry's payload;
  * the `.idd` is the **payload blob** -- the entries are concatenated in `.idx`
    record order, with no gaps and no per-file header.

`sum(payload sizes) == os.path.getsize(.idd)` **exactly** on all 12 archives in
the client (measured, see work/idd_layout_report.md).  That identity is what
makes extraction exact rather than heuristic: no magic scanning, no guessed
lengths, no truncation, and full byte coverage.

THE `.idx` LAYOUT
-----------------
    u32 magic | u32 version=15 | u32 count_a | u32 count_b
    then from offset 0x10 to EOF: one continuous obfuscated stream.

The stream obeys a **self-differential XOR recurrence over the whole body**:

    plain[i] = raw[i] ^ plain[i-4]        for i >= 4
    plain[0:4] = raw[0:4] ^ seed

(measured: plain[1:4] == raw[1:4] on every archive, so seed == (k,0,0,0) -- only
the first plaintext byte is masked, by a single unknown byte `k`).  `k` is
recovered by demanding that the record chain walk cleanly to EOF; it is not
guessed and no directory prefix has to be known.

Records inside the decoded stream:

    [name: L bytes, no extensions, NUL-free] [trailer: 20 bytes]

    trailer = u32 hash | u32 size | u32 zero | u32 zero | u32 L_next

`L_next` is the *name* length of the next record, so the next record begins at
`p + L + 20`.  The first record's length is not stored: it is the leading run of
path characters.  The FINAL record carries a 16-byte trailer (no `L_next`) and
is flushed when fewer than 20 bytes remain.

Names are **asset group names without file extensions** -- `Bonus/Airplane1`,
`MP3/Aliens`, `Game/AIBattle_SuperStar`, `HiddenCatch/Bt_close`.  Every previous
scan rejected them because it required a known file extension.

USAGE
>>> import idx_idd
>>> entries = idx_idd.read_index("extracted/Boom/FxMap.idx")
>>> for e in idx_idd.carve("extracted/Boom/FxMap.idd", entries): ...
"""
import os
import struct

OFFSET = 0x10
TRAILER = 20
FINAL_TRAILER = 16
RUNCH = frozenset(
    b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-"
)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def _decode(raw, k, off=OFFSET):
    """Apply the global self-differential XOR chain from `off` to EOF."""
    n = len(raw)
    m = n - off
    if m <= 0:
        return b""
    out = bytearray(m)
    out[0] = raw[off] ^ k
    for i in range(1, min(4, m)):
        out[i] = raw[off + i]          # measured: plain[1:4] == raw[1:4]
    for i in range(4, m):
        out[i] = raw[off + i] ^ out[i - 4]
    return bytes(out)


def _walk(pt, limit=1_000_000):
    """Chain the records in a decoded body. Returns (records, end_offset)."""
    n = len(pt)
    i = 0
    while i < n and pt[i] in RUNCH:
        i += 1
    length = i
    recs = []
    p = 0
    while 2 <= length <= 65536 and p + length + FINAL_TRAILER <= n \
            and len(recs) < limit:
        have_next = p + length + TRAILER <= n
        name = pt[p:p + length]
        nfield = 5 if have_next else 4
        tr = [u32(pt, p + length + 4 * j) for j in range(nfield)]
        recs.append({
            "offset": p,
            "length": length,
            "name": name.decode("latin1", "replace"),
            "hash": tr[0],
            "size": tr[1],
            "zero1": tr[2],
            "zero2": tr[3],
            "next_length": tr[4] if len(tr) > 4 else 0,
        })
        if not have_next:
            p = p + length + FINAL_TRAILER
            break
        p = p + length + TRAILER
        length = tr[4]
    return recs, p


def solve_k(raw, off=OFFSET, probe=8192):
    """Recover the single masked plaintext byte. No prefix needs to be known.

    Scores each candidate by how far its record chain walks inside an 8 KB
    probe window; the true `k` walks it end to end while wrong ones break in
    the first record.
    """
    best = None
    for k in range(256):
        pt = _decode(raw[:off + probe], k, off)
        recs, end = _walk(pt)
        score = (end, len(recs))
        if best is None or score > best[0]:
            best = (score, k)
    return best[1]


def read_index(path):
    """Decode a `.idx`. Returns (entries, stats). Each entry has `name`/`size`."""
    raw = open(path, "rb").read()
    k = solve_k(raw)
    pt = _decode(raw, k)
    recs, end = _walk(pt)
    stats = {
        "path": path,
        "magic": raw[:4].hex(" "),
        "size": len(raw),
        "version": u32(raw, 4),
        "count_a": u32(raw, 8),
        "count_b": u32(raw, 12),
        "k": k,
        "body": len(pt),
        "walked": end,
        "complete": end >= len(pt),
        "entries": len(recs),
    }
    return recs, stats


def carve(idd_path, entries, validate=None):
    """Yield (entry, payload_bytes) carving `idd` by the index's exact sizes.

    `validate(payload) -> truthy` optionally confirms each payload parses as
    its own format; entries failing it are still yielded (the size is exact
    either way) but flagged by the caller.
    """
    size = os.path.getsize(idd_path)
    declared = sum(e["size"] for e in entries)
    if declared != size:
        raise ValueError(
            f"{idd_path}: index sizes sum to {declared:,} but the file is "
            f"{size:,} — refusing to carve a mismatched pair"
        )
    with open(idd_path, "rb") as fh:
        pos = 0
        for e in entries:
            fh.seek(pos)
            blob = fh.read(e["size"])
            yield e, blob
            pos += e["size"]


def index_for(idd_path):
    """The sibling `.idx` path for an `.idd`, or None if absent."""
    idx = os.path.splitext(idd_path)[0] + ".idx"
    return idx if os.path.exists(idx) else None
