import os,re,collections,json,sys
BOOM="/Users/hieu/Workspaces/taone/extracted/Boom"
# asset path: optional dir/ then stem with an asset extension
EXT=r'(?:bmp|dds|tga|png|jpg|jpeg|ani|scr|eff|ogg|tmb|msk|bik)'
PATH=re.compile((r'([A-Za-z0-9_][A-Za-z0-9_\-./\\]{1,90}?\.'+EXT+r')\b').encode())
# also bare quoted names / img="..." attributes
ATTR=re.compile(rb'(?:img|Img|IMG|BackPath|AniPath|Path|Name|File)\s*=\s*["\']?([A-Za-z0-9_][A-Za-z0-9_\-./]{2,80})')
FULL=re.compile(rb'/(?:Quest|PopupEvent|Icon|Item|Shop|Event|EventPopup|ShopTop)\b')
found=collections.defaultdict(set)
counts=collections.Counter()
for root,_,fs in os.walk(BOOM):
    for f in fs:
        p=os.path.join(root,f)
        try: d=open(p,'rb').read()
        except: continue
        rel=os.path.relpath(p,BOOM)
        for m in PATH.finditer(d):
            s=m.group(1).decode('latin-1').replace('\\','/')
            if s.startswith('./'): s=s[2:]
            found[rel].add(s)
            counts[rel]+=1
tot=sum(len(v) for v in found.values())
print("files with asset paths:",len(found),"total distinct:",tot)
for k in sorted(found,key=lambda k:-len(found[k]))[:45]:
    print("  %-42s %d"%(k,len(found[k])))
json.dump({k:sorted(v) for k,v in found.items()}, open("/tmp/idd_paths.json","w"), indent=1)
print("wrote /tmp/idd_paths.json")
# prefix histogram
pre=collections.Counter()
alls=set()
for v in found.values(): alls|=v
for s in alls: pre[s.rsplit('/',1)[0] if '/' in s else '(root)']+=1
print("=== top dir prefixes ===")
for k,c in pre.most_common(30): print("   %-40s %d"%(k,c))
print("=== total distinct asset paths ===",len(alls))
