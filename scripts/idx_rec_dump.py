#!/usr/bin/env python3
"""Careful single-record dump for the big `ca da ef` .idx family.

Establishes: name decode, name length, and what follows the NUL.
"""
import sys, struct, os

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")
EXTS = (b".bmp", b".dds", b".ogg", b".ani", b".scr", b".tga", b".jpg", b".jpeg",
        b".png", b".luc", b".txt", b".ini", b".xml", b".wav", b".bik", b".cur",
        b".slk", b".fft", b".dat", b".mp3", b".spr", b".img", b".act", b".eff")
PREFIXES = [b"Game/", b"Quest/", b"PopupEvent/", b"Bonus/", b"Sound/", b"Item/",
            b"Map/", b"Character/", b"Stage/", b"Contents/", b"Desktop/",
            b"Effect/", b"Fx/", b"Data/", b"Image/", b"Texture/", b"Avatar/",
            b"Pet/", b"Npc/", b"Event/", b"Bg/", b"Common/", b"Back/",
            b"Loading/", b"Interface/", b"Ui/", b"Model/", b"Anim/", b"Font/",
            b"Movie/", b"Voice/", b"Icon/", b"Cash/", b"Mode/", b"Rhythm/",
            b"Monument/", b"Hidden/", b"Monster/", b"Music/"]


def dec_name(raw, p, seed, cap=512):
    m = min(cap, len(raw) - p)
    out = bytearray(m)
    for i in range(m):
        out[i] = raw[p + i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(out)


def derive(raw, p, cap=512):
    """Try each known 4-char prefix -> seed; keep strictly-valid paths."""
    cands = []
    for pfx in PREFIXES:
        if len(pfx) < 4 or p + 4 > len(raw):
            continue
        seed = bytes(raw[p + i] ^ pfx[i] for i in range(4))
        pt = dec_name(raw, p, seed, cap)
        L = 0
        while L < len(pt) and pt[L] in PATHCH:
            L += 1
        if L < len(pfx) + 3:
            continue
        nm = pt[:L]
        if pt[L] != 0:
            continue
        if nm[:len(pfx)] != pfx:
            continue
        if not nm.lower().endswith(EXTS):
            continue
        if b"//" in nm or b"/." in nm:
            continue
        cands.append((L, seed, nm))
    cands.sort(key=lambda t: -t[0])
    return cands


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def main():
    idx = open(sys.argv[1], "rb").read()
    p = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x10
    show = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    print(f"{os.path.basename(sys.argv[1])} size={len(idx):,} start={p:#x}")
    for r in range(show):
        cands = derive(idx, p)
        if not cands:
            print(f"  @{p:#x}: no derived name")
            # raw dump anyway
            print("    raw:", idx[p:p+48].hex(" "))
            break
        L, seed, nm = cands[0]
        print(f"  rec{r} @{p:#x} seed={seed.hex(' ')} L={L} name={nm.decode('latin1')!r}")
        if len(cands) > 1:
            print(f"       (other cands: {[(c[0], c[2].decode('latin1')) for c in cands[1:3]]})")
        q = p + L + 1                      # byte after NUL
        raw_after = idx[q:q + 32]
        print(f"    after-NUL raw @{q:#x}: {raw_after.hex(' ')}")
        # plaintext-as-is u32s
        vals = [u32(idx, q + 4 * k) for k in range(5)]
        print(f"    plaintext u32s: {vals}")
        # chained u32s (continue chain: dec offset q.. with last 4 plain bytes)
        pt = dec_name(idx, q, bytes(4), 64)  # naive
        # proper: last 4 plaintext chars of the name
        last4 = nm[-4:]
        seedc = bytes(idx[q + i] ^ last4[i] for i in range(4))
        ptc = dec_name(idx, q, seedc, 64)
        cvals = [u32(ptc, 4 * k) for k in range(5)]
        print(f"    chained   u32s: {cvals}")
        print(f"    chained  bytes: {ptc[:40].hex(' ')}")
        # guess: next record starts where? show next few positions where derive() succeeds
        found = []
        for d in range(4, 80):
            if derive(idx, q + d):
                found.append(q + d)
        print(f"    next derivable offsets within 80B: {[hex(x) for x in found[:6]]}")
        # also try: next name at p+L+1+16
        nxt = q + 16
        print(f"    derive at q+16={nxt:#x}: {derive(idx,nxt) and derive(idx,nxt)[0][2].decode('latin1')!r}")
        if found:
            p = found[0]
        else:
            break


if __name__ == "__main__":
    main()
