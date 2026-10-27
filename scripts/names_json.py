#!/usr/bin/env python3
"""Mine Club Audition / Boom decoded data for asset & package names -> work/names.json

Sources (read-only):
  extracted/Boom/vh/*.bmp        34 UI sprites, real filenames
  extracted/Boom/ndadata/*       91 popup bundles, real filenames
  extracted/Boom/**/*.idd        UI layout scripts; PLAINTEXT asset paths inside
  work/ssi/*.bin                 decoded ssi1 containers ([u32len][payload] records)

Two clearly separated tiers are emitted:
  HARD  - verbatim plaintext (vh stems, ndadata stems, idd script paths)
  SOFT  - ASCII records recovered from decoded .bin via length-prefix records
See work/names_report.md.
"""
import os, re, json, struct, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names_records import scan_ascii, best_korean_chain, korean_payload

ROOT = "/Users/hieu/Workspaces/taone"
SSI  = os.path.join(ROOT, "work/ssi")
BOOM = os.path.join(ROOT, "extracted/Boom")
OUT  = os.path.join(ROOT, "work/names.json")

by_source = collections.OrderedDict()
tier      = {}                                   # source -> "hard"/"soft"
ext_counts = collections.Counter()
ext_example= collections.defaultdict(set)

def add(src, name, t="soft"):
    if not name: return
    if re.search(r'\s', name): return          # no spaces (sentences)
    by_source.setdefault(src, set()).add(name)
    tier[src] = t

NAME_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_\-]{2,}$')
PATH_RE = re.compile(r'^[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-./]+)+$')
STOP = set("""the and for you are not all any can use new add del set get test
none random space name type item icon shop info time date size mode data file
open save close back next ok cancel yes no on off up down left right start stop
play pause exit quit help list view edit copy paste undo redo true false null
empty full half zero two three four five six seven eight nine ten this that
with from into over under more less than then player server room user pass word
credit cash point level grade rank normal battle ready stage map game menu option
config sound music press click select using used value values result error
""".split())
def keep(s):
    if not (NAME_RE.match(s) or PATH_RE.match(s)): return False
    if s.lower() in STOP: return False
    if re.fullmatch(r'[0-9_\-]+', s): return False
    if re.search(r'\s', s): return False            # no spaces (sentences)
    stem = s.rsplit('/', 1)[-1]
    if re.fullmatch(r'[0-9_\-]+', stem): return False   # digit-only stem
    return bool(re.search(r'[A-Za-z]{2}', stem))

EXT_LIST = ("bmp dds tga png jpg jpeg ogg wav mp3 ond ani scr msk eff bik bnk "
            "tmb dat ini ssd idx idd pak fft ttf exe dll cfg log aes").split()
ASSET_PATH_RE = re.compile(
    rb'([A-Za-z0-9_][A-Za-z0-9_\-./\\]{1,90}?\.(?:%s))\b' % b'|'.join(x.encode() for x in EXT_LIST), re.I)

def note_ext(s):
    m = re.search(r'\.([A-Za-z]{2,4})$', s)
    if m:
        e = m.group(1).lower()
        if e in EXT_LIST:
            ext_counts[e] += 1; ext_example[e].add(s[:70])

# ---------------------------------------------------------- HARD: vh
for fn in sorted(os.listdir(os.path.join(BOOM, "vh"))):
    if fn.lower().endswith(".bmp"):
        add("vh", fn[:-4], "hard")

# ---------------------------------------------------------- HARD: ndadata
nda = os.path.join(BOOM, "ndadata")
stems = {os.path.splitext(f)[0] for f in os.listdir(nda)}
for s in sorted(stems): add("ndadata", s, "hard")

# ---------------------------------------------------------- HARD: .idd scripts
for root, _, fs in os.walk(BOOM):
    for f in fs:
        if not f.lower().endswith(".idd"): continue
        try: d = open(os.path.join(root, f), "rb").read()
        except OSError: continue
        for m in ASSET_PATH_RE.finditer(d):
            s = m.group(1).decode("latin-1").replace("\\", "/").lstrip("./")
            if s.startswith("/"): s = s[1:]
            if "/" in s and keep(s.rsplit("/",1)[-1]) or ("/" in s and re.search(r'[A-Za-z]{2}', s)):
                add("idd_scripts", s, "hard"); note_ext(s)

# ----------------------------------------- SOFT: decoded ssi .bin records
SOURCES = {
    "fxstagemap.ssd.bin": "fxstagemap", "fxdynmapinfo.ssd.bin": "fxdynmapinfo",
    "fxdynimginfo.ssd.bin": "fxdynimginfo", "fxstock0.ini.bin": "fxstock",
    "fxstock1.ini.bin": "fxstock", "fxstock2.ini.bin": "fxstock",
    "fxstock3.ini.bin": "fxstock", "csysstr.ssd.bin": "csysstr",
    "csysqstr.ssd.bin": "csysqstr", "csysfxmg.ssd.bin": "csysfxmg",
    "stringtable.ini.bin": "stringtable", "multisvr.ssd.bin": "multisvr",
    "spcc.ssd.bin": "spcc", "filterstr.ssd.bin": "filterstr",
    "fxstovi.ini.bin": "fxstovi", "packagemap.ini.bin": "packagemap",
    "product.ini.bin": "product",
}
struct_report = {}
for fn, src in SOURCES.items():
    p = os.path.join(SSI, fn)
    if not os.path.exists(p): continue
    d = open(p, "rb").read()
    # non-overlapping ASCII records from validated length prefixes
    recs = scan_ascii(d)
    nonover = []; last = -1
    for off, L, pay in sorted(recs):
        if off > last:
            nonover.append((off, L, pay)); last = off + 4 + L
    kor = best_korean_chain(d)
    struct_report[src] = {
        "size": len(d),
        "ascii_records_all_offsets": len(recs),
        "ascii_records_nonoverlapping": len(nonover),
        "ascii_coverage": round(sum(4+L for _,L,_ in nonover)/len(d), 3),
        "korean_records_chained": len(kor),
    }
    for off, L, pay in nonover:
        s = pay.decode("ascii").strip()
        note_ext(s)
        if keep(s): add(src, s)
    for off, L, pay in kor:
        try: s = pay.decode("cp949").strip()
        except Exception: continue
        note_ext(s)
        if keep(s): add(src, s)

# extension census across the whole tree (background context)
for root, _, fs in os.walk(BOOM):
    for f in fs:
        try: d = open(os.path.join(root, f), "rb").read()
        except OSError: continue
        for m in re.finditer(rb'\.([A-Za-z]{2,4})(?![A-Za-z0-9])', d):
            e = m.group(1).decode().lower()
            if e in EXT_LIST: ext_counts[e] += 1

# ---------------------------------------------------------------- assemble
AUX_SOURCES = {"filterstr"}          # profanity blacklist, not asset names
cand = set()
for k, names in by_source.items():
    if k not in AUX_SOURCES: cand |= names
candidates = sorted(cand, key=lambda s: (s.lower(), s))
ASSET_EXTS = [e for e in ("bmp","dds","tga","png","jpg","jpeg","ani","scr","ogg",
                          "wav","mp3","tmb","msk","eff","bik","dat","ini","ssd",
                          "idd","idx","pak","fft","ttf") if ext_counts.get(e)]
out = {
    "candidates": candidates,
    "by_source": {k: sorted(v, key=lambda s: (s.lower(), s)) for k, v in by_source.items()},
    "extensions": ASSET_EXTS,
    "count": len(candidates),
    "_meta": {
        "generator": "scripts/names_json.py",
        "tiers": {k: tier.get(k, "soft") for k in by_source},
        "aux_sources": sorted(AUX_SOURCES),
        "source_counts": {k: len(v) for k, v in by_source.items()},
        "struct_report": struct_report,
        "extension_hits": dict(ext_counts.most_common()),
        "extension_examples": {k: sorted(v)[:4] for k, v in ext_example.items()},
    },
}
json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
chk = json.load(open(OUT))
assert chk["count"] == len(chk["candidates"])
print("wrote", OUT, "count", chk["count"], "(JSON verified)")
print("extensions:", ASSET_EXTS)
for k, v in by_source.items():
    print("   %-14s %-5s %5d" % (k, tier.get(k), len(v)))
