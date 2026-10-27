import struct, sys, collections
d=open("/Users/hieu/Workspaces/taone/work/ssi/packagemap.ini.bin","rb").read()
print("size",len(d))
# try u32 LE at each of 4 alignments; count plausible small ints
for off in range(4):
    vals=[struct.unpack_from('<I',d,i)[0] for i in range(off,len(d)-3,4)]
    small=sum(1 for v in vals if 0<v<100000)
    print("align %d: n=%d small=%d (%.0f%%) min=%d max=%d"%(off,len(vals),small,100*small/len(vals),min(vals),max(vals)))
# alignment 2 hypothesis: first u16 count then u32 pairs
import collections
vals=[struct.unpack_from('<I',d,i)[0] for i in range(2,len(d)-3,4)]
print("align2 first 20:",vals[:20])
print("align2 last 10:",vals[-10:])
# group into pairs
pairs=list(zip(vals[0::2],vals[1::2]))
print("npairs",len(pairs))
print("pairs[:20]",pairs[:20])
left=collections.Counter(a for a,b in pairs); right=collections.Counter(b for a,b in pairs)
print("distinct left",len(left),"distinct right",len(right))
print("left most common",left.most_common(10))
print("right most common",right.most_common(10))
print("u16 at 0 =",struct.unpack_from('<H',d,0)[0])
