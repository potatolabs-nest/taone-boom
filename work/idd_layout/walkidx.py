"""Walk a ca da ef .idx and decode record names.

Cipher (NOTES.md §8):  name[i] = stem[i] ^ name[i-4], i>=4
For i<4 the seed is unknown; we derive it from the known leading directory
("Game/" etc).  The name is NUL-terminated.

Record layout:  stem[name_len] (name_len includes the NUL)  | u32 A | u32 A | u32 0 | u32 X
"""
import sys, os, struct
B = '/Users/hieu/Workspaces/taone/extracted/Boom'


def decode_name(stem, prefix):
    """Return (name_bytes, consumed) or (None, None)."""
    if len(stem) < 4:
        return None, None
    seed = bytes(stem[i] ^ prefix[i] for i in range(4))
    out = bytearray()
    for i in range(0, len(stem)):
        if i < 4:
            c = stem[i] ^ seed[i]
        else:
            c = stem[i] ^ out[i - 4]
        if c == 0:
            return bytes(out), i + 1
        out.append(c)
        if len(out) > 260:
            return None, None
    return None, None


def walk(name, prefix, limit=None):
    x = open(os.path.join(B, name + '.idx'), 'rb').read()
    n = len(x)
    print(f"=== {name}.idx {n:,}  magic={x[:4].hex(' ')}  hdr={[struct.unpack_from('<I',x,i)[0] for i in range(4,16,4)]}")
    pos = 0x10
    recs = []
    bad = 0
    while pos < n:
        if pos + 4 > n:
            break
        nm, used = decode_name(x[pos:], prefix)
        if nm is None:
            bad += 1
            print(f"  FAIL at {pos:#x}: stem={x[pos:pos+32].hex(' ')}")
            break
        fields_off = pos + used
        if fields_off + 16 > n:
            print(f"  short tail at {pos:#x}")
            break
        A, A2, Z, X = struct.unpack_from('<IIII', x, fields_off)
        recs.append((pos, nm.decode('cp949', 'replace'), A, A2, Z, X, used))
        if len(recs) <= 6:
            print(f"  {pos:#08x} len={used:3d} A={A:>10,} A2={A2:>10,} Z={Z} X={X:>10}  {nm.decode('cp949','replace')!r}")
        pos = fields_off + 16
        if limit and len(recs) >= limit:
            break
    print(f"  records={len(recs)}  endpos={pos:#x} ({pos})  filesize={n:#x}  exact={pos==n}")
    bad_names = [r for r in recs if b'\x00' in r[1].encode('cp949', 'replace')]
    nonprint = [r for r in recs if not all(32 <= ord(c) < 127 for c in r[1])]
    print(f"  non-ascii names: {len(nonprint)}")
    return recs


if __name__ == '__main__':
    nm = sys.argv[1] if len(sys.argv) > 1 else 'FxStage'
    pre = (sys.argv[2] if len(sys.argv) > 2 else 'Game/').encode()
    walk(nm, pre)
