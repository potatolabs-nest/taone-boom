#!/usr/bin/env python3
"""Global lag scan: find every lag with an anomalously LOW mean |delta|.
A raster or any periodic layout shows up as a sharp minimum; a 1-D sequence
shows only the lag-3 channel minimum.
"""
import struct
import sys
import zlib
from collections import Counter


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load(p):
    b = open(p, "rb").read()
    if len(b) > 8 and u32(b, 0) == len(b) - 8:
        b = zlib.decompress(b[8:])
    c = u32(b, 0)
    hdr = 24 + 48 * c
    ent = [[u32(b, o + 4 * j) for j in range(12)]
           for o in range(24, 24 + 48 * c, 48)]
    rest = b[hdr:]
    N = u32(rest, 0)
    return ent, rest[4:4 + N]


def main():
    p = sys.argv[1]
    ent, blk = load(p)
    n = len(blk)
    e = ent[0]
    print(f"{p}\n entry0={e} block={n} w={e[6]} h={e[7]} "
          f"w*h={e[6]*e[7]} ratio={n/(e[6]*e[7]):.4f}")
    maxlag = min(n - 1, int(sys.argv[2]) if len(sys.argv) > 2 else 3000)
    budget = 3000
    res = []
    for lag in range(1, maxlag + 1):
        st = max(1, (n - lag) // budget)
        s = 0
        c = 0
        for i in range(0, n - lag, st):
            s += abs(blk[i] - blk[i + lag])
            c += 1
        res.append((s / c, lag))
    med = sorted(x[0] for x in res)[len(res) // 2]
    print(f" median delta = {med:.2f}")
    res.sort()
    print(" 20 lowest-delta lags:")
    for d, lag in res[:20]:
        tag = ""
        if lag % 3 == 0:
            tag = f"  lag/3={lag//3}"
        print(f"   lag={lag:6d} delta={d:7.2f} rel={d/med:.3f}{tag}")
    print(" 20 highest-delta lags:")
    for d, lag in res[-20:]:
        print(f"   lag={lag:6d} delta={d:7.2f} rel={d/med:.3f}")


if __name__ == "__main__":
    main()
