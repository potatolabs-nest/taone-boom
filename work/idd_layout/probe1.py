"""Recover the name stream from a ca da ef .idx body.

The cipher is name[i] = stem[i] ^ name[i-4].  So the decoded name splits into 4
independent residue-class streams, each determined up to a single unknown byte
(XOR constant).  For a class to be a printable path, there must be a constant
making every character printable.  Enumerate those constants.
"""
import sys, os, collections

B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def streams(stem):
    """Return 4 lists a_r[k] = xor of stem[r+4], stem[r+8] ... stem[r+4k]."""
    out = [[] for _ in range(4)]
    for r in range(4):
        acc = 0
        for i in range(r + 4, len(stem), 4):
            acc ^= stem[i]
            out[r].append(acc)
    return out


def candidates(vals, lo=32, hi=126, max_c=8):
    """bytes v in 0..255 such that v ^ x is printable for all x in vals"""
    good = []
    for c in range(256):
        ok = True
        for x in vals:
            ch = c ^ x
            if ch < lo or ch > hi:
                ok = False
                break
        if ok:
            good.append(c)
    return good[:max_c]


def main():
    name = sys.argv[1]
    start = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x10
    ln = int(sys.argv[3], 0) if len(sys.argv) > 3 else 128
    d = open(os.path.join(B, name + '.idx'), 'rb').read()
    stem = d[start:start + ln]
    print(f"{name}.idx size={len(d)} stem@{start:#x} len={ln}")
    ss = streams(stem)
    for r in range(4):
        # try the printable-filter with a growing prefix length
        for take in (len(ss[r]), 24, 16, 12, 8, 6, 4):
            take = min(take, len(ss[r]))
            cs = candidates(ss[r][:take])
            if cs:
                print(f"  class {r}: take={take} -> const {[hex(c) for c in cs]}")
                break
        else:
            print(f"  class {r}: no printable constant")


if __name__ == '__main__':
    main()
