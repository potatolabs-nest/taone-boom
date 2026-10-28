import struct, sys, os
B='/Users/hieu/Workspaces/taone/extracted/Boom'
name=sys.argv[1]
p=os.path.join(B,name+'.idd')
d=open(p,'rb').read()
n=len(d)
print(f"{name} size={n:,}")
A,Bv,C=struct.unpack_from('<III',d,0)
print(f"u32[0]=A={A}  u32[1]=2  u32[2]=B={Bv}  u32[3]=C={C}")
# print first 200 u32 with index
for i in range(0,200):
    v=struct.unpack_from('<i',d,i*4)[0]
    if i%8==0:
        print(f"\n{i:4d}: ", end='')
    print(f"{v:>12d}", end=' ')
print()
