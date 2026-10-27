import re,os,struct,json
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom/ndadata"
EXT=r'(?:bmp|dds|tga|png|jpg|jpeg|ani|scr|eff|ogg|tmb|msk|bik)'
NP=re.compile((r'[A-Za-z0-9_./\-]{2,90}?\.'+EXT+r'\b').encode())
report={}
for f in sorted(os.listdir(BOOM)):
    if not f.endswith(".idd"): continue
    stem=f[:-4]; d=open(os.path.join(BOOM,f),'rb').read()
    names=sorted(set(m.group(0).decode('latin-1') for m in NP.finditer(d)))
    ix=os.path.join(BOOM,stem+".idx")
    idn=None
    if os.path.exists(ix):
        x=open(ix,'rb').read()
        idn=(len(x), struct.unpack_from('<I',x,8)[0], struct.unpack_from('<I',x,12)[0])
    if names or idn:
        report[stem]=(names,idn)
# focus: 21thBirthPopUp
for stem in ("21thBirthPopUp","FindNote","TwoDayFlow01","SelectCandy","WelcomeToBnB"):
    names,idn=report.get(stem,([],None))
    print("=== %s  names=%d idx=%s"%(stem,len(names),idn))
    for n in names[:40]: print("    ",n)
# size test: if this is the exact name set, sum(prefix+len+12)==idxsize-16 for some prefix len
print()
print("=== size consistency test (assume prefix u32 + name + 12 trailing) ===")
for stem in ("21thBirthPopUp","FindNote","TwoDayFlow01","SelectCandy"):
    names,idn=report.get(stem,([],None))
    if not idn: continue
    sz,c8,c12=idn
    if not names: continue
    tot=sum(4+len(n)+12 for n in names)
    print("  %-18s idx=%d c8=%d c12=%d  sum(4+nm+12)=%d  diff=%d  (n=%d)"%(
        stem,sz,c8,c12,tot,sz-16-tot,len(names)))
