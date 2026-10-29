#!/usr/bin/env python3
"""Validate the .table header law across all records and characterise the
24-byte prefix.

Law under test: header_len == 24 + 48*count, where count == u32[0].
Validation is independent of the law: a record is CONFIRMED when some u32 at
offset k*4 satisfies u32 == filesize - (k*4 + 4) (an exact self-length field),
and that k*4 == 24 + 48*count.
"""
import glob
import os
import struct
from collections import Counter

ASSETS = "/Users/hieu/Workspaces/taone/work/assets/by_index"


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def len_field_index(b):
    n = len(b) // 4
    for i in range(2, n):
        v = u32(b, 4 * i)
        if 0 < v and 4 * (i + 1) + v == len(b):
            return i
    return None


def main():
    tot = 0
    law_holds = 0
    confirmed = 0
    confirmed_and_law = 0
    prefix = [Counter() for _ in range(6)]
    p1_eq_2 = 0
    p0_eq_count = 0
    count_max = 0
    for arch in sorted(os.listdir(ASSETS)):
        d = os.path.join(ASSETS, arch)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.table"))):
            b = open(f, "rb").read()
            if len(b) < 24:
                continue
            tot += 1
            c = u32(b, 0)
            count_max = max(count_max, c)
            hdr = 24 + 48 * c
            if hdr <= len(b):
                law_holds += 1
            if u32(b, 4) == 2:
                p1_eq_2 += 1
            for j in range(6):
                prefix[j][u32(b, 4 * j)] += 1
            k = len_field_index(b)
            if k is not None:
                confirmed += 1
                if 4 * k == hdr:
                    confirmed_and_law += 1
    print(f"total .table records        : {tot:,}")
    print(f"header fits 24+48*count     : {law_holds:,} ({law_holds/tot*100:.2f}%)")
    print(f"u32[1] == 2                 : {p1_eq_2:,} ({p1_eq_2/tot*100:.2f}%)")
    print(f"record-verified (exact len field exists): {confirmed:,}")
    print(f"  ...and that field sits exactly at 24+48*count: {confirmed_and_law:,} "
          f"({confirmed_and_law/max(confirmed,1)*100:.2f}%)")
    print(f"max count = {count_max}")
    print("prefix field value distributions:")
    for j in range(6):
        print(f"  u32[{j}]: {prefix[j].most_common(6)}  distinct={len(prefix[j])}")


if __name__ == "__main__":
    main()
