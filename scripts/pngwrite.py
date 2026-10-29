#!/usr/bin/env python3
"""Minimal PNG writer (stdlib only) + renderers for candidate .table layouts."""
import struct
import zlib


def png(path, w, h, pix, mode="RGB"):
    """pix: bytes, len == w*h*nch."""
    nch = {"RGB": 3, "RGBA": 4, "L": 1}[mode]
    assert len(pix) == w * h * nch, (len(pix), w * h * nch)
    ct = {"L": 0, "RGB": 2, "RGBA": 6}[mode]
    raw = bytearray()
    stride = w * nch
    for y in range(h):
        raw.append(0)
        raw += pix[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 6)))
        f.write(chunk(b"IEND", b""))
    return path


def stats(pix):
    n = len(pix)
    mean = sum(pix) / n
    var = sum((b - mean) ** 2 for b in pix) / n
    from collections import Counter
    c = Counter(pix)
    return {"n": n, "mean": mean, "std": var ** 0.5, "distinct": len(c),
            "frac_top": c.most_common(1)[0][1] / n, "top": c.most_common(4)}
