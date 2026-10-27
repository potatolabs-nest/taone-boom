import os,re,collections,struct,glob
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom"
SSI="/Users/hieu/Workspaces/taone/work/ssi"
hits=collections.Counter(); ex=collections.defaultdict(list)
KNOWN="bmp dds tga png jpg jpeg ogg wav mp3 ond ani scr msk eff bik bnk tmb dat ini ssd idx idd pak fft ttf tga".split()
# scan .idx (all, incl ndadata) for plaintext ".ext"
files=[]
for root,_,fs in os.walk(BOOM):
    for f in fs:
        if f.lower().endswith((".idx",".idd",".pak",".ssd",".ini",".dat",".cfg")):
            files.append(os.path.join(root,f))
for p in files:
    d=open(p,'rb').read()
    for m in re.finditer(rb'[ -~]{0,40}\.([A-Za-z]{2,4})[^A-Za-z0-9]', d):
        e=m.group(1).decode().lower()
        if e in KNOWN:
            hits[e]+=1
            if len(ex[e])<6: ex[e].append(m.group(0)[:40].decode('latin-1'))
    # also raw ".ext" without trailing char
    for m in re.finditer(rb'\.(bmp|dds|tga|png|jpg|jpeg|ogg|ani|scr|msk|eff|bik|tmb)\b', d):
        e=m.group(1).decode().lower(); hits["RAW_"+e]+=1
print("=== plaintext .ext in archives ===")
for e,c in hits.most_common(40):
    print("  %-10s %-6d %s"%(e,c,ex.get(e.replace("RAW_",""),[])[:3]))
