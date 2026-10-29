#!/usr/bin/env python3
"""Brute-force the engine's sprite pixel codec by rendering candidates.

The descriptor is known: u32 kind | u32 2 | u32 frames | u32 0 | u32 width |
u32 height, then a frame table. What is unknown is where pixel data starts and
how it is encoded.

Rather than guess analytically, generate a grid of plausible decodings, write
them as PNGs, and inspect them. Stdlib only (zlib + struct) so no PIL needed.

Usage: python3 -I crack_sprite.py <sprite-file> <outdir>
"""
import os, struct, sys, zlib


def write_png(path, w, h, rgb):
    """rgb: bytes of length w*h*3."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)                       # filter type 0
        raw += rgb[y * stride:(y + 1) * stride]
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def candidates(d, w, h, start):
    """Yield (label, width, height, rgb bytes)."""
    body = d[start:]
    n = w * h

    # 1. raw RGB
    if len(body) >= n * 3:
        yield ("rgb_%d" % start, w, h, body[:n * 3])
    # 2. raw RGBA (drop alpha)
    if len(body) >= n * 4:
        rgb = bytearray()
        for i in range(n):
            o = i * 4
            rgb += body[o:o + 3]
        yield ("rgba_%d" % start, w, h, bytes(rgb))
    # 3. BGR / ABGR variants
    if len(body) >= n * 4:
        rgb = bytearray()
        for i in range(n):
            o = i * 4
            rgb += bytes((body[o + 2], body[o + 1], body[o]))
        yield ("abgr_%d" % start, w, h, bytes(rgb))
    if len(body) >= n * 3:
        rgb = bytearray()
        for i in range(n):
            o = i * 3
            rgb += bytes((body[o + 2], body[o + 1], body[o]))
        yield ("bgr_%d" % start, w, h, bytes(rgb))

    # 4. greyscale / 8bpp
    if len(body) >= n:
        rgb = bytearray()
        for i in range(n):
            v = body[i]
            rgb += bytes((v, v, v))
        yield ("gray_%d" % start, w, h, bytes(rgb))

    # 5. 16bpp (565 and 5551)
    if len(body) >= n * 2:
        for lab, shift, mask_r, mask_g, mask_b in (
                ("rgb565", 0, 0xF800, 0x07E0, 0x001F),
                ("rgba5551", 0, 0xF800, 0x07C0, 0x003E)):
            rgb = bytearray()
            for i in range(n):
                v = body[i * 2] | (body[i * 2 + 1] << 8)
                r = (v & mask_r) >> 11 if mask_r == 0xF800 else 0
                g = (v & mask_g) >> (5 if mask_r == 0xF800 else 6)
                b = (v & mask_b)
                rgb += bytes(((r * 255) // 31, (g * 255) // 63 if mask_g == 0x07C0 else (g * 255) // 31, (b * 255) // 31))
            yield ("%s_%d" % (lab, start), w, h, bytes(rgb))


def main():
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    d = open(src, "rb").read()
    kind, f2, frames, zero, w, h = struct.unpack_from("<6I", d, 0)
    print(f"kind={kind} frames={frames} w={w} h={h} size={len(d)}")

    made = 0
    # try a range of start offsets around the end of the frame table
    for start in (24, 32, 36, 40, 44, 276, 280, 284, 288, 292):
        if start >= len(d):
            continue
        for lab, cw, ch, rgb in candidates(d, w, h, start):
            name = f"{lab}_{cw}x{ch}.png"
            write_png(os.path.join(outdir, name), cw, ch, rgb)
            made += 1
    print(f"wrote {made} candidates to {outdir}")


if __name__ == "__main__":
    main()
