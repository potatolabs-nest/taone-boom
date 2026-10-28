#!/usr/bin/env python3
"""Recover the true 4-byte seed of a big-idx head without assuming (k,0,0,0).

dec[i] = stem[i] ^ dec[i-4] means the four residue classes mod 4 are
independent XOR chains, each seeded by one byte of the seed. So each seed byte
can be solved on its own by picking the value that makes that chain printable.
"""
import sys

PATHCH = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_/.-")


def solve_seed(stem, term=0x00, nterm=6):
    """Return (seed, plaintext) maximizing printable path chars."""
    L = len(stem)
    seed = [0] * 4
    for j in range(4):
        best = None
        for s in range(256):
            x = s ^ stem[j]
            chain = [x]
            k = j + 4
            while k < L:
                x = x ^ stem[k]
                chain.append(x)
                k += 4
            # score: printable run from the start; stop at terminator
            good = 0
            for c in chain:
                if c in PATHCH:
                    good += 1
                elif c < 32:
                    good += 2  # NUL/control terminator ok
                    break
                else:
                    break
            sc = good
            if best is None or sc > best[0]:
                best = (sc, s, bytes(chain))
        seed[j] = best[1]
    # now decrypt
    out = bytearray(L)
    for i in range(L):
        out[i] = stem[i] ^ (seed[i] if i < 4 else out[i - 4])
    return bytes(seed), bytes(out)


def main():
    idx = open(sys.argv[1], "rb").read()
    off = int(sys.argv[2], 0) if len(sys.argv) > 2 else 16
    ln = int(sys.argv[3]) if len(sys.argv) > 3 else 48
    seed, pt = solve_seed(idx[off:off + ln])
    print(f"offset {off:#x}: seed={seed.hex(' ')}")
    print(f"  plain: {pt!r}")
    print(f"  tail (undecodable past terminator): {pt[:pt.find(b'\x00') if b'\x00' in pt else len(pt)]!r}")


if __name__ == "__main__":
    main()
