"""Reliable record extraction from decoded ssi .bin blobs.

Structure established (see names_report.md):
  * ASCII name tables : [u32 len][ASCII bytes] ... repeatedly
  * Korean UI tables  : [u32 len][CP949 bytes] chained
  * stringtable.ini   : [u16 index][u32 len][CP949 bytes]  (100% coverage)
We detect ASCII records by length-prefix validation at every offset (no
chaining), and Korean records by chained walks. Validated by counting how
many records the recovered length prefixes account for.
"""
import struct

def ascii_payload(b):
    return b and all(0x20 <= c < 0x7f for c in b)

def scan_ascii(d, maxlen=512):
    """Every offset where [u32 L][L strict-ASCII bytes] validates."""
    n = len(d); out = []
    for p in range(0, n - 4):
        L = struct.unpack_from('<I', d, p)[0]
        if 1 <= L <= maxlen and p + 4 + L <= n:
            pay = d[p+4:p+4+L]
            if ascii_payload(pay):
                out.append((p, L, pay))
    return out

def korean_payload(b):
    if not b: return False
    try:
        s = b.decode('cp949')
    except Exception:
        return False
    if not s: return False
    good = sum(1 for ch in s if ch.isprintable() or ch in '\r\n\t')
    return good >= len(s) * 0.98

def chain(d, start, skip, maxlen=8192, pred=korean_payload):
    n = len(d); i = start; out = []
    while i + skip + 4 <= n:
        L = struct.unpack_from('<I', d, i + skip)[0]
        if not (1 <= L <= maxlen) or i + skip + 4 + L > n: break
        pay = d[i+skip+4:i+skip+4+L]
        if not pred(pay): break
        out.append((i+skip+4, L, pay)); i += skip + 4 + L
    return out

def best_korean_chain(d, maxlen=8192):
    best = []
    for start in range(0, 32):
        for skip in (0, 1, 2, 4):
            r = chain(d, start, skip, maxlen)
            if len(r) > len(best): best = r
    return best
