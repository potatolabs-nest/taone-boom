#!/usr/bin/env python3
"""For every .table record, test payload_size against w*h at 1/2/3/4 bpp."""
import glob
import os
import struct
from collections import Counter, defaultdict

ROOT = "/Users/hieu/Workspaces/taone"
ASSETS = os.path.join(ROOT, "work/assets/by_index")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def analyze(path):
    b = open(path, "rb").read()
    if len(b) < 8:
        return None
    c = u32(b, 0)
    hdr = 24 + 48 * c
    if hdr > len(b):
        return None
    tail = b[hdr:]
    # entry rect hypothesis: f6,f7 = (w,h)
    areas = []
    whs = []
    for e in range(c):
        o = 24 + 48 * e
        f0, f1 = u32(b, o), u32(b, o + 4)
        w, h = u32(b, o + 24), u32(b, o + 28)
        whs.append((w, h))
        areas.append(w * h)
    return {"path": path, "size": len(b), "count": c, "hdr": hdr,
            "tail": len(tail), "areas": areas, "whs": whs,
            "tail0": u32(b, hdr) if len(tail) >= 4 else None}


def main():
    for arch in ("FxStage", "CharTE", "FxCharacter", "FxMap"):
        files = sorted(glob.glob(os.path.join(ASSETS, arch, "*.table")))
        rel = Counter()
        exact = Counter()
        for f in files:
            r = analyze(f)
            if not r:
                continue
            tl = r["tail"]
            sa = sum(r["areas"])
            # what if tail = u32 len + data ?
            if tl >= 4 and u32(open(f, "rb").read(), r["hdr"]) == tl - 4:
                tl2 = tl - 4
            else:
                tl2 = tl
            for bpp in (1, 2, 3, 4):
                if sa and sa * bpp == tl:
                    exact[(f"sumarea*{bpp}",)] += 1
                if sa and sa * bpp == tl2:
                    exact[(f"(sumarea*{bpp})",)] += 1
            if tl2 and sa:
                rel[round(tl2 / sa, 3)] += 1
        print(f"# {arch}: {len(files)} files")
        print(f"  exact matches: {exact.most_common(10)}")
        print(f"  top tail/sumarea ratios: {rel.most_common(10)}")
        print()


if __name__ == "__main__":
    main()
