#!/usr/bin/env python3
"""Build the self-contained Artifact version of the rhythm game.

Artifacts are ONE html file with no external media, so every song and sprite is
inlined as a data URI. That forces a size budget: the rendered page must stay
under 16 MB and base64 costs ~1.37x. Songs are the expensive part, so a spread
of ten is chosen rather than all 693.

The artifact is also not a standalone document: the host wraps the file in its
own <!doctype>/<head>/<body>, so this emits title + style + markup + script and
no document scaffolding.

Usage: python3 -I build_artifact.py
"""
import base64, json, os, re, sys

ROOT = "/Users/hieu/Workspaces/taone"
TEMPLATE = os.path.join(ROOT, "deploy/index.html")
OUT = os.path.join(ROOT, "app/artifact/audition-web.html")
MANIFEST = os.path.join(ROOT, "work/assets/manifest.json")

BUDGET = 9_000_000                # headroom under the 16 MB artifact cap
TITLE = "Audition Web"

FONT_LINK = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2'
             '?family=Chakra+Petch:wght@500;600;700&display=swap">')


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def must(hay, needle, what):
    if needle not in hay:
        sys.exit(f"TEMPLATE CHANGED — {what} not found:\n  {needle[:90]}")
    return hay.replace(needle, "", 0)   # presence check only


def build_manifest():
    man = json.load(open(MANIFEST))
    songs = [a for a in man["assets"] if a.get("format") == "ogg" and a.get("size")]
    songs.sort(key=lambda a: a["size"])
    usable = [s for s in songs if 150_000 < s["size"] < 620_000] or songs

    N = 10
    picked = ([usable[int(i * len(usable) / N)] for i in range(N)]
              if len(usable) >= N else usable)

    assets, used = [], 0
    for i, a in enumerate(picked):
        raw = os.path.join(ROOT, "work/assets", a["file"])
        if not os.path.exists(raw):
            continue
        data = b64(raw)
        if used + len(data) > BUDGET * 0.78:
            break
        used += len(data)
        assets.append({
            "id": "FxSound/%06d" % i, "archive": "FxSound", "index": i,
            "offset": a.get("offset", 0), "size": a.get("size", 0),
            "format": "ogg", "mime": "audio/ogg", "name": None,
            "file": "data:audio/ogg;base64," + data, "confidence": "high",
        })

    # Prefer the menu artwork that actually reads at small size; skip the
    # 600 KB+ atlases so the songs fit.
    WANT = ["Prepare_PRE_Bt_Ready", "Lobby_Normal_bt01", "Lobby_Battle_bt01",
            "UXMatching_RoomUI_Bt_QuickStart", "Etc_BtOk", "GlobalUI_BtMenu",
            "Prepare_PRE_Bt_Selectmap", "Lobby_Gametype_bt01",
            "UxMatching_RoomUI_Bt_AllRoom", "UXMatching_RoomUI_Bt_Ladder",
            "GlobalUI_BtShop", "Etc_BtCancel"]
    sprites = []
    for s in man.get("ui_sprites", []):
        if s.get("name") not in WANT:
            continue
        raw = os.path.join(ROOT, "work/assets", s["file"])
        if not os.path.exists(raw):
            continue
        data = b64(raw)
        if used + len(data) > BUDGET:
            continue
        used += len(data)
        sprites.append({"name": s["name"], "file": "data:image/bmp;base64," + data,
                        "width": s.get("width", 0), "height": s.get("height", 0),
                        "size": s.get("size", 0)})

    return {
        "generated": man.get("generated", ""),
        "summary": {"total_assets": len(assets), "by_format": {"ogg": len(assets)},
                    "by_archive": {"FxSound": len(assets)},
                    "ui_sprites": len(sprites), "ndadata_pak": 0},
        "archives": [{"name": "FxSound", "idd_size": 0, "asset_count": len(assets)}],
        "assets": assets, "ui_sprites": sprites, "ndadata": [],
    }


def main():
    src = open(TEMPLATE).read()

    title = re.search(r"<title>([^<]*)</title>", src)
    title = title.group(1) if title else TITLE
    style = re.search(r"<style>(.*?)</style>", src, re.S)
    if not style:
        sys.exit("no <style> block in template")
    css = style.group(1)

    body = re.search(r"<body>(.*?)<script>", src, re.S)
    if not body:
        sys.exit("no body markup in template")
    markup = body.group(1).strip()

    script = re.search(r"<script>\s*\"use strict\";(.*?)</script>", src, re.S)
    if not script:
        sys.exit("no main script in template")
    js = script.group(1)

    # ---------- CSS: commit to one dark arcade theme ------------------
    must(css, "padding-left:var(--gutter); padding-right:var(--gutter);", "body gutter")
    css = css.replace(
        "padding-left:var(--gutter); padding-right:var(--gutter);",
        "padding-left:max(16px, env(safe-area-inset-left, 0px));\n"
        "    padding-right:max(16px, env(safe-area-inset-right, 0px));", 1)

    # the host pins color-scheme: light, so a dark page must say so itself
    css = css.replace(
        "  :root{\n    --bg:#0b0f17;",
        "  :root{\n    color-scheme: dark;\n    --bg:#0b0f17;", 1)

    # drop the light-mode override: a rhythm stage is a dark world by design
    css = re.sub(r"\s*@media \(prefers-color-scheme: light\)\{.*?\n  \}", "", css, count=1, flags=re.S)

    # display face for headings/score, system sans for running text
    css = css.replace(
        "--font: ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif;",
        "--font: ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif;\n"
        "    --display: \"Chakra Petch\", ui-sans-serif, system-ui, sans-serif;", 1)
    css = css.replace("h1{font-size:22px;margin:0;letter-spacing:.3px}",
                      "h1{font-family:var(--display);font-size:24px;font-weight:700;margin:0;letter-spacing:.4px}", 1)
    css = css.replace(".score{font-size:26px;font-weight:700;line-height:1}",
                      ".score{font-family:var(--display);font-size:28px;font-weight:700;line-height:1}", 1)
    css += ("\n  /* the stage is the product: give it room and a lit edge */\n"
            "  .stage{box-shadow:0 0 0 1px #ffffff0d, 0 18px 50px -18px #ff4fa355}\n"
            "  @media (prefers-reduced-motion: reduce){ .judge.on{animation:none;opacity:1} }\n")

    # ---------- JS: inline assets, read data: URIs, survive a republish ----
    must(js, "if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(p)) return null;", "safePath guard")
    js = js.replace(
        "if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(p)) return null;   // any scheme",
        "if (/^data:(audio|image)\\/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]+$/i.test(p)) return p;\n"
        "  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(p)) return null;   // any other scheme", 1)

    must(js, 'fetch("manifest.json", {cache:"no-store"})', "manifest fetch")
    js = js.replace(
        'fetch("manifest.json", {cache:"no-store"})\n'
        '    .then(function(r){ if(!r.ok) throw new Error("manifest HTTP "+r.status); return r.json(); })\n',
        'Promise.resolve(window.__MANIFEST__)\n', 1)

    must(js, '/* ============================ state =============================== */', "state marker")
    js = js.replace(
        '/* ============================ state =============================== */',
        '/* Data URIs are decoded here: no network, and fetch() semantics for a\n'
        '   data: URL vary, so decode explicitly. */\n'
        'function toArrayBuffer(src){\n'
        '  var i = src.indexOf(",");\n'
        '  var bin = atob(src.slice(i+1));\n'
        '  var out = new Uint8Array(bin.length);\n'
        '  for (var k=0;k<bin.length;k++) out[k] = bin.charCodeAt(k);\n'
        '  return out.buffer;\n'
        '}\n\n'
        '/* ============================ state =============================== */', 1)

    js = js.replace(
        'fetch(p).then(function(r){\n    if (!r.ok) throw new Error("HTTP "+r.status);\n    return r.arrayBuffer();\n  }).then(function(buf){',
        'Promise.resolve(toArrayBuffer(p)).then(function(buf){', 1)
    js = js.replace(
        'fetch(p).then(function(r){ return r.arrayBuffer(); }).then(function(buf){',
        'Promise.resolve(toArrayBuffer(p)).then(function(buf){', 1)

    # the asset browser is not published with the game
    js = re.sub(r'\n?// the asset browser lives.*?\n\}\)\(\);\n', "\n", js, flags=re.S)
    js = re.sub(r'\n?fetch\("browser\.html".*?\n\}\);\n', "\n", js, flags=re.S)
    js = js.replace('$("btnBrowse").addEventListener("click", function(){ location.href = "index.html"; });',
                    '$("btnBrowse").classList.add("hide");', 1)

    # keep the player where they were across a republish
    js = js.replace(
        "boot();\n",
        "window.__hot = (window.claude && window.claude.hot) || null;\n"
        "function snapshot(){\n"
        "  try { if (window.__hot) window.__hot.snapshot({\n"
        "    song: selected ? selected.id : null, diff: $(\"diff\").value, spd: $(\"spd\").value });\n"
        "  } catch(e){}\n"
        "}\n"
        "function start(prev){\n"
        "  boot();\n"
        "  try {\n"
        "    if (prev && prev.diff) $(\"diff\").value = prev.diff;\n"
        "    if (prev && prev.spd) $(\"spd\").value = prev.spd;\n"
        "    if (prev && prev.song && SONGS.length){\n"
        "      for (var i=0;i<SONGS.length;i++) if (SONGS[i].id === prev.song){ pick(SONGS[i]); break; }\n"
        "    }\n"
        "  } catch(e){}\n"
        "  setInterval(snapshot, 4000);\n"
        "}\n"
        "if (window.__hot && window.__hot.ready) window.__hot.ready(start);\n"
        "else start(window.__hot ? window.__hot.data : {});\n", 1)

    man = build_manifest()
    out = (
        f"<title>{title}</title>\n"
        f'<meta name="claude:viewport-fit-sides" content="cover">\n'
        f"{FONT_LINK}\n"
        f"<style>{css}</style>\n"
        f"{markup}\n"
        f"<script>window.__MANIFEST__ = {json.dumps(man, separators=(',', ':'))};</script>\n"
        f'<script>"use strict";{js}</script>\n'
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write(out)

    size = os.path.getsize(OUT)
    print(f"songs inlined : {len(man['assets'])}")
    print(f"sprites inlined: {len(man['ui_sprites'])}")
    print(f"output        : {OUT}")
    print(f"size          : {size/1024:,.0f} KB ({size/1_048_576:.2f} MB)")
    # precise: <header> must not trip a bare "<head" substring check
    for pat in (r"<!doctype", r"<html[\s>]", r"<head[\s>]", r"<body[\s>]",
                r"</html\s*>", r"</head\s*>", r"</body\s*>"):
        if re.search(pat, out, re.I):
            sys.exit(f"document scaffolding leaked: {pat}")
    if size > 16_000_000:
        sys.exit("over the 16 MB artifact limit")


if __name__ == "__main__":
    main()
