#!/usr/bin/env python3
"""Pin down the pixel geometry of `FxStage/00561_Lobby__Monster2_bt01.table`,
which corresponds to the plaintext BMP `extracted/Boom/vh/Lobby_Monster2_bt01.bmp`
(171x880 24bpp).  The block clearly holds BGRA bytes (alpha 0xff every 4).
"""
import struct
import sys


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


tb = "/Users/hieu/Workspaces/taone/work/assets/by_index/FxStage/00561_Lobby__Monster2_bt01.table"
bp = "/Users/hieu/Workspaces/taone/extracted/Boom/vh/Lobby_Monster2_bt01.bmp"

b = open(tb, "rb").read()
c = u32(b, 0)
hdr = 24 + 48 * c
blk = b[hdr:]
print(f"count={c} hdr={hdr} blk={len(blk)}")

print("alpha(0xff) fraction by phase mod 4:")
for p in range(4):
    seg = blk[p::4]
    print(f"  phase {p}: {seg.count(255)/len(seg)*100:5.1f}%  ({len(seg)} bytes)")

print("first 40 u32:", [u32(blk, 4 * i) for i in range(10)])
# find where alpha starts being regular
for start in range(0, 64):
    ok = sum(1 for i in range(start, min(start + 400, len(blk)), 4)
             if blk[i] == 255)
    tot = len(range(start, min(start + 400, len(blk)), 4))
    if ok / tot > 0.9:
        print(f"  alpha-regular from offset {start}: {ok}/{tot}")
        break

rb = open(bp, "rb").read()
w, h = struct.unpack_from("<ii", rb, 18)
off = struct.unpack_from("<I", rb, 10)[0]
stride = ((w * 3) + 3) // 4 * 4
print(f"bmp {w}x{h} stride={stride} pix={len(rb)-off}")


def bmp_row_top(y):
    """BMP rows are bottom-up; return top-row y as BGR bytes (no padding)."""
    ob = off + (h - 1 - y) * stride
    return rb[ob:ob + w * 3]


# Build BGRA for the top row and search it in the block
row = bmp_row_top(0)
for alpha in (255, 0):
    cand = bytearray()
    for x in range(w):
        B, G, R = row[3 * x], row[3 * x + 1], row[3 * x + 2]
        cand += bytes([B, G, R, alpha])
    for start in range(0, 64):
        idx = blk.find(bytes(cand[:256]), start)
        if idx >= 0:
            print(f"  BGRA(alpha={alpha}) row0 first256 found at {idx} (search from {start})")
            break
    else:
        print(f"  BGRA(alpha={alpha}) row0 NOT found")
    # also try RGBA
    cand2 = bytearray()
    for x in range(w):
        B, G, R = row[3 * x], row[3 * x + 1], row[3 * x + 2]
        cand2 += bytes([R, G, B, alpha])
    idx = blk.find(bytes(cand2[:256]))
    print(f"  RGBA(alpha={alpha}) row0 first256 at {idx}")
