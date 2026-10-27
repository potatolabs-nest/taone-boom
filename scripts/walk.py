import sys, struct, os
p=sys.argv[1]; d=open(p,'rb').read()
print(f"=== {os.path.basename(p)} size={len(d)}")
# Find every plausible [u16 len][name] with a printable-ish name
cands=[]
for o in range(16, len(d)-2):
    L=struct.unpack_from('<H', d, o)[0]
    if 1<=L<=200 and o+2+L<=len(d):
        nm=d[o+2:o+2+L]
        pr=sum(1 for b in nm if 32<=b<127)
        if pr==L:  # fully printable
            cands.append((o,L,nm))
print("fully-printable [u16 len][name] candidates:", len(cands))
for o,L,nm in cands[:25]:
    print(f"   @{o:<7} len={L:<4} {nm!r}   tail={d[o+2+L:o+2+L+16].hex(' ')}")
