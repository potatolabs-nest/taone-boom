import struct, sys, os
B='/Users/hieu/Workspaces/taone/extracted/Boom'
name=sys.argv[1]
off=int(sys.argv[2],0)
ln=int(sys.argv[3]) if len(sys.argv)>3 else 256
d=open(os.path.join(B,name+'.idd'),'rb').read()
n=len(d)
start=max(0,off-ln//2)
chunk=d[start:start+ln]
print(f"{name} around 0x{off:x} (abs {off})  file={n:,}")
for i in range(0,len(chunk),16):
    a=start+i
    row=chunk[i:i+16]
    hexs=' '.join(f'{b:02x}' for b in row)
    asc=''.join(chr(b) if 32<=b<127 else '.' for b in row)
    mark='<<<' if a<=off<a+16 else '   '
    print(f"{a:>10} 0x{a:08x} {hexs:<48} {asc} {mark}")
