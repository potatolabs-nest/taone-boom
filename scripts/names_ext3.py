import os,re,collections
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom"
SSI="/Users/hieu/Workspaces/taone/work/ssi"
CAND=re.compile(rb'\.([A-Za-z]{2,4})(?![\-A-Za-z0-9_])')
KNOWN=set("bmp dds tga png jpg jpeg ogg wav mp3 ond ani scr msk eff bik bnk tmb dat ini ssd idx idd pak fft ttf exe dll cfg log aes".split())
hits=collections.Counter(); ex=collections.defaultdict(set)
for base in (BOOM,SSI):
    for root,_,fs in os.walk(base):
        for f in fs:
            p=os.path.join(root,f)
            try: d=open(p,'rb').read()
            except: continue
            for m in CAND.finditer(d):
                e=m.group(1).decode().lower()
                if e in KNOWN:
                    hits[e]+=1
                    if len(ex[e])<8: ex[e].add(d[max(0,m.start()-30):m.end()].decode('latin-1'))
print("=== extension token counts across ALL game files ===")
for e,c in hits.most_common(): print("  %-6s %-7d %s"%(e,c,sorted(ex[e])[:3]))
