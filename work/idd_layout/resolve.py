"""Brute force the ca da ef record layout.

Record 0 decodes cleanly with prefix Game/.  Assume a fixed fields region of
width W after the stem, plus a possible plaintext name tail.  Search W in 0..40
and require the *whole* record chain to decode to valid paths until EOF.
"""
import struct, os, sys
B = '/Users/hieu/Workspaces/taone/extracted/Boom'
OK = set(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-. /~+()[]@")


def dec(d, p, prefix, maxlen=200):
    if p + 4 > len(d):
        return None
    seed = bytes(a ^ b for a, b in zip(d[p:p + 4], prefix[:4]))
    out = bytearray()
    for i in range(maxlen):
        if p + i >= len(d):
            return None
        c = d[p + i] ^ (seed[i] if i < 4 else out[i - 4])
        if c == 0:
            return i + 1, bytes(out)
        if c not in OK:
            return None
        out.append(c)
    return None


def try_walk(name, prefix, W, extra=0):
    d = open(os.path.join(B, name + '.idx'), 'rb').read()
    n = len(d)
    p = 0x10
    recs = 0
    while p < n:
        r = dec(d, p, prefix)
        if r is None:
            return recs, p, False
        stemlen, nm = r
        if not nm.startswith(prefix):
            return recs, p, False
        p = p + stemlen + W + extra
        recs += 1
        if recs > 5000:
            break
    return recs, p, True


name = sys.argv[1] if len(sys.argv) > 1 else 'FxStage'
prefix = (sys.argv[2] if len(sys.argv) > 2 else 'Game/').encode()
print(f"=== {name} prefix={prefix!r}")
best = []
for W in range(0, 41):
    r, p, exact = try_walk(name, prefix, W)
    if r >= 3:
        best.append((r, W, p, exact))
best.sort(reverse=True)
for r, W, p, exact in best[:12]:
    print(f"  W={W:3d} records={r:5d} end={p:#x} exact={exact}")
