import os,re,collections,json
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom"
RUN=re.compile(rb'[ -~]{5,}')
EXT=re.compile(rb'\.(?:bmp|dds|tga|png|jpg|jpeg|ani|scr|eff|ogg|tmb|msk|bik)\b',re.I)
tot=0; files=0; allnames=set(); per=collections.Counter()
for root,_,fs in os.walk(BOOM):
    for f in fs:
        if not f.lower().endswith((".idx",".idd")): continue
        p=os.path.join(root,f); d=open(p,'rb').read()
        runs=[m.group(0).decode('latin-1') for m in RUN.finditer(d)]
        hits=[r for r in runs if EXT.search(r.encode('latin-1'))]
        if hits:
            files+=1; tot+=len(hits)
            for h in hits: allnames.add(h); per[os.path.relpath(p,BOOM)]+=1
print("files with printable asset-name runs:",files,"runs:",tot,"distinct:",len(allnames))
for k,c in per.most_common(25): print("   %-45s %d"%(k,c))
json.dump(sorted(allnames), open("/tmp/idx_ascii_names.json","w"), indent=1)
print("wrote /tmp/idx_ascii_names.json")
for s in sorted(allnames)[:60]: print("   ",s)
