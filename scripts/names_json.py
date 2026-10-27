import sys, os, struct, json, re, collections

ROOT = "/Users/hieu/Workspaces/taone"
SSI  = os.path.join(ROOT, "work/ssi")
BOOM = os.path.join(ROOT, "extracted/Boom")
OUT  = os.path.join(ROOT, "work/names.json")

by_source = collections.OrderedDict()
def add(src, name):
    if not name: return
    by_source.setdefault(src, set()).add(name)

def printable(b):
    return all(0x20 <= c < 0x7f for c in b)

def lp_strings(d, maxlen=512):
    """Walk u32-length-prefixed ASCII strings; return list of (offset,str)."""
    n=len(d); i=0; out=[]
    while i+4 <= n:
        L=struct.unpack_from('<I', d, i)[0]
        if 1 <= L <= maxlen and i+4+L <= n and printable(d[i+4:i+4+L]):
            out.append((i, d[i+4:i+4+L].decode('ascii'))); i += 4+L
        else:
            i += 1
    return out

# ---- NAME FILTER ------------------------------------------------------
NAME_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_\-]{2,}$')
PATH_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_\-]*(/[A-Za-z0-9_\-]+)+$')
SENT_RE = re.compile(r'[ <>{}\[\]|@#$%^&*()=+~`"\'\\:,;?!]')
def is_name(s):
    if NAME_RE.match(s): return True
    if PATH_RE.match(s): return True
    return False

# generic english words / ui sentences to reject
STOP = set("""the and for you are not all any can use new add del set get
test none random space name type item icon shop info time date size mode
data file open save close back next ok cancel yes no on off up down left right
start stop play pause exit quit help list view edit copy paste undo redo
true false null none empty full half zero one two three four five six seven
eight nine ten this that with from into over under more less than then
player server room user pass word credit cash point level grade rank
normal battle ready stage map mode game menu option config sound music
""".split())
def reject_common(s):
    return s.lower() in STOP

# ---- 1. vh sprites ----------------------------------------------------
vhd = os.path.join(BOOM, "vh")
for fn in sorted(os.listdir(vhd)):
    if fn.lower().endswith(".bmp"):
        add("vh", fn[:-4])

# ---- 2. ndadata bundle stems -----------------------------------------
nda = os.path.join(BOOM, "ndadata")
stems = set()
for fn in sorted(os.listdir(nda)):
    base, ext = os.path.splitext(fn)
    stems.add(base)
for s in sorted(stems):
    add("ndadata", s)

# ---- 3. structural parse of decoded .bin -----------------------------
SSI_MAP = {
  "fxstagemap.ssd.bin": "fxstagemap",
  "fxdynmapinfo.ssd.bin": "fxdynmapinfo",
  "fxdynimginfo.ssd.bin": "fxdynimginfo",
  "fxstock0.ini.bin": "fxstock0", "fxstock1.ini.bin": "fxstock1",
  "fxstock2.ini.bin": "fxstock2", "fxstock3.ini.bin": "fxstock3",
  "csysstr.ssd.bin": "csysstr", "csysqstr.ssd.bin": "csysqstr",
  "filterstr.ssd.bin": "filterstr", "stringtable.ini.bin": "stringtable",
  "multisvr.ssd.bin": "multisvr", "csysfxmg.ssd.bin": "csysfxmg",
  "spcc.ssd.bin": "spcc", "fxstovi.ini.bin": "fxstovi",
}
exts = collections.Counter(); ext_ctx = collections.defaultdict(set)
struct_report = {}
for fn, src in SSI_MAP.items():
    p = os.path.join(SSI, fn)
    if not os.path.exists(p): continue
    d = open(p, "rb").read()
    # best start offset
    best=[]; 
    for s in range(0,24):
        r=lp_strings(d[s:]) if s==0 else [(o+s,t) for o,t in lp_strings(d[s:])]
        if len(r)>len(best): best=r
    struct_report[src]=(len(best), sum(4+len(t) for _,t in best), len(d))
    for off, s in best:
        if s.lower().endswith(tuple("."+e for e in
              ("bmp dds tga png jpg jpeg ogg ani scr msk eff bik avi wav mp3 tmb dat ini ssd idx idd pak fft ttf".split()))):
            e=s.rsplit(".",1)[1].lower(); exts[e]+=1; ext_ctx[e].add(s)
        if is_name(s) and not reject_common(s):
            add(src, s)

# raw extension scan across ALL bins + strings
for fn in sorted(os.listdir(SSI)):
    p=os.path.join(SSI,fn)
    d=open(p,'rb').read()
    for m in re.finditer(rb'[A-Za-z0-9_\-/]{1,60}\.([A-Za-z][A-Za-z0-9]{1,4})\b', d):
        e=m.group(1).decode().lower()
        if e in ("bmp dds tga png jpg jpeg ogg ani scr msk eff bik avi wav mp3 tmb dat ini ssd idx idd pak fft ttf exe dll dat".split()):
            exts[e]+=1

# ---- 4. root-level ssi files (esfn, CALauncher, 720897) ---------------
for fn in ("esfn.ssd","CALauncher.cfg","720897.dat","720897_NGM_v2"):
    p=os.path.join(BOOM,fn)
    if not os.path.exists(p): continue
    d=open(p,'rb').read()
    for _,s in lp_strings(d):
        if is_name(s) and not reject_common(s): add("root_ssi", s)
    for m in re.finditer(rb'[A-Za-z][A-Za-z0-9_\-]{2,40}', d):
        s=m.group(0).decode()
        if is_name(s): add("root_ssi", s)

# ---- 5. strings.txt regex fallback (path-ish tokens) ------------------
for fn in sorted(os.listdir(SSI)):
    if not fn.endswith(".strings.txt"): continue
    src=fn[:-len(".strings.txt")]+"_txt"
    txt=open(os.path.join(SSI,fn),encoding="latin-1").read()
    for m in re.finditer(r'[A-Za-z][A-Za-z0-9_\-]{2,}(?:/[A-Za-z0-9_\-]+)*', txt):
        s=m.group(0)
        if s.lower() in ("font","color","div","br","nbsp"): continue
        if is_name(s) and not reject_common(s): add(src, s)

# ---- assemble ---------------------------------------------------------
extensions = sorted(exts, key=lambda e:-exts[e])
cand = set()
for src, names in by_source.items():
    cand |= names
candidates = sorted(cand, key=lambda s:(s.lower(), s))

out = {
  "candidates": candidates,
  "by_source": {k: sorted(v, key=lambda s:(s.lower(),s)) for k,v in by_source.items()},
  "extensions": extensions,
  "count": len(candidates),
  "_meta": {
    "generated_by": "scripts/names_json.py",
    "struct_report": {k:{"strings":v[0],"covered":v[1],"total":v[2]} for k,v in struct_report.items()},
    "extension_hits": dict(exts),
    "source_counts": {k:len(v) for k,v in by_source.items()},
  },
}
json.dump(out, open(OUT,"w"), indent=1)
print("wrote", OUT)
print("count", len(candidates))
for k,v in by_source.items(): print("  %-20s %d"%(k,len(v)))
print("extensions:", extensions)
