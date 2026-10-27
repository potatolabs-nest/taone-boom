import struct,os
SSI="/Users/hieu/Workspaces/taone/work/ssi"
def hdr_u16(d): return struct.unpack_from('<H',d,0)[0]

# packagemap
d=open(SSI+"/packagemap.ini.bin",'rb').read()
n=hdr_u16(d); need=2+n*8
print("packagemap: u16@0=%d  needs 2+%d*8=%d  filesize=%d  EXACT=%s"%(n,n,need,len(d),need==len(d)))

# product
d=open(SSI+"/product.ini.bin",'rb').read()
print("product: u16@0=%d  size=%d"%(hdr_u16(d),len(d)))
# try header pattern: many tables -> count then entries

# csysfxmg: [u16 count][u8 flag][u32 len][cp949]*
d=open(SSI+"/csysfxmg.ssd.bin",'rb').read()
cnt=hdr_u16(d); i=3; ok=0
while i+4<=len(d):
    L=struct.unpack_from('<I',d,i)[0]
    if not(1<=L<=4000) or i+4+L>len(d): break
    try: d[i+4:i+4+L].decode('cp949')
    except: break
    ok+=1; i+=4+L
print("csysfxmg: u16 count=%d  parsed=%d  end=%d/%d  flag byte@2=%d"%(cnt,ok,i,len(d),d[2]))

# csysstr: alternating [u32 keylen][ascii key][u32 vallen][cp949 value]
d=open(SSI+"/csysstr.ssd.bin",'rb').read()
i=0; pairs=0; mism=0
while i+4<=len(d):
    L1=struct.unpack_from('<I',d,i)[0]
    if not(1<=L1<=4000) or i+4+L1+4>len(d): mism+=1;break
    k=d[i+4:i+4+L1]
    try: k.decode('ascii')
    except: mism+=1;break
    j=i+4+L1
    L2=struct.unpack_from('<I',d,j)[0]
    if not(1<=L2<=8000) or j+4+L2>len(d): mism+=1;break
    v=d[j+4:j+4+L2]
    ok_enc=False
    for e in ('cp949','ascii'):
        try: v.decode(e); ok_enc=True;break
        except: pass
    if not ok_enc: mism+=1;break
    pairs+=1; i=j+4+L2
print("csysstr: alternating key/value pairs=%d  consumed=%d/%d  misalign=%d"%(pairs,i,len(d),mism))
print("   sample:", [ (d[p:p+20]) for p in [0]] )
# channel2
d=open(SSI+"/channel2_001.ssd.bin",'rb').read()
print("channel2: u16@0=%d u16@2=%d size=%d  (2+n*48=?)"%(hdr_u16(d),struct.unpack_from('<H',d,2)[0],len(d)))
n=hdr_u16(d); print("   if 2+n*48:", 2+n*48, " if n*48:", n*48)
