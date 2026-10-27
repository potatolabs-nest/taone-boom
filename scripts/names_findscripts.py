import os,re,collections
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom"
pat=re.compile(rb'[ -~]{2,60}\.(?:bmp|dds|tga|png|jpg|jpeg|ani|scr|eff|ogg|tmb)\b')
loc=collections.defaultdict(list)
for root,_,fs in os.walk(BOOM):
    for f in fs:
        p=os.path.join(root,f)
        try: d=open(p,'rb').read()
        except: continue
        for m in pat.finditer(d):
            s=m.group(0).decode('latin-1')
            if '/' in s or '\\' in s:
                loc[os.path.relpath(p,BOOM)].append((m.start(),s))
for k in sorted(loc, key=lambda k:-len(loc[k])):
    v=loc[k]
    print("=== %-45s %d hits"%(k,len(v)))
    for off,s in v[:6]:
        print("      @0x%x %s"%(off,s))
