import sys, struct, os, json, collections, re

SSI = sys.argv[1] if len(sys.argv) > 1 else "/Users/hieu/Workspaces/taone/work/ssi"

def printable(b):
    return all(0x20 <= c < 0x7f for c in b)

def parse_lp(d, start, stride_hint=0):
    """Walk u32-len-prefixed strings from `start`."""
    i = start; n = len(d); out = []
    while i + 4 <= n:
        L = struct.unpack_from('<I', d, i)[0]
        if L == 0:
            i += 4; continue
        if 1 <= L <= 512 and i + 4 + L <= n and printable(d[i+4:i+4+L]):
            out.append((i, L, d[i+4:i+4+L].decode('ascii')))
            i += 4 + L
        else:
            i += 1
    return out

best_results = {}
for fn in sorted(os.listdir(SSI)):
    if not fn.endswith('.bin'): continue
    d = open(os.path.join(SSI, fn), 'rb').read()
    best = []
    for s in range(0, 24):
        r = parse_lp(d, s)
        if len(r) > len(best):
            best = r
    # coverage = bytes explained by (4+strlen)
    cov = sum(4+lr[1] for lr in best)
    best_results[fn] = (best, cov, len(d))

for fn, (recs, cov, total) in best_results.items():
    print("%-28s recs=%-6d cov=%d/%d (%.1f%%)" % (fn, len(recs), cov, total, 100.0*cov/max(total,1)))
    seen = set(); show = []
    for off, L, s in recs:
        if s not in seen:
            seen.add(s); show.append(s)
    for s in show[:8]:
        print("      ", repr(s))
