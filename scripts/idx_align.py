import sys,struct
d=open(sys.argv[1],'rb').read()
# records end with tail  [00 00 00 00][u32 nameLen][pad?]  -- actually nameLen precedes name
# find positions of 0x1a..0x00 00 00 00 pattern -> tail marker '00 00 00 00 00'
marks=[i for i in range(16,len(d)-5) if d[i:i+5]==b'\x00\x00\x00\x00\x00']
print("marker count",len(marks))
# record boundary: nameLen(u32) then name then ... then marker then ...
# print spacing between consecutive marks
print("first marks:",[hex(m) for m in marks[:30]])
print("gaps:",[marks[i+1]-marks[i] for i in range(min(30,len(marks)-1))])
