#!/usr/bin/env python3
"""Build the static site deployed to GitHub Pages.

Produces ./deploy : the game plus a curated, size-bounded slice of the real
extracted assets (a spread of songs and the menu sprites). Everything it
writes is regenerable from Boom.zip, so ./deploy is not committed.

Usage: python3 -I build_deploy.py
"""
import json, os, shutil, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_GAME = os.path.join(ROOT, "app/public/game.html")
ASSETS = os.path.join(ROOT, "work/assets")
MANIFEST = os.path.join(ASSETS, "manifest.json")
OUT = os.path.join(ROOT, "deploy")

N_SONGS = 60


def main():
    if not os.path.exists(MANIFEST):
        sys.exit("run scripts/extract_assets.py first — no manifest at " + MANIFEST)
    man = json.load(open(MANIFEST))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "FxSound"))
    os.makedirs(os.path.join(OUT, "vh"))

    # the playable client shell is the landing page; the rhythm game is kept
    # alongside it as a direct-entry route
    client = os.path.join(ROOT, "app/public/client.html")
    shutil.copy(client if os.path.exists(client) else SRC_GAME,
                os.path.join(OUT, "index.html"))
    if os.path.exists(client):
        shutil.copy(SRC_GAME, os.path.join(OUT, "game.html"))
    # keep Pages from running Jekyll over the output
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    songs = [a for a in man["assets"] if a.get("format") == "ogg" and a.get("size")]
    songs.sort(key=lambda a: a["size"])
    usable = [s for s in songs if 190_000 < s["size"] < 460_000] or songs
    if len(usable) >= N_SONGS:
        step = len(usable) / N_SONGS
        picked = [usable[int(i * step)] for i in range(N_SONGS)]
    else:
        picked = usable

    # real in-game names, decoded from the index (verified byte-exact)
    names = {}
    npath = os.path.join(ROOT, "work/asset_names.json")
    if os.path.exists(npath):
        names = json.load(open(npath))

    out_assets = []
    for i, a in enumerate(picked):
        src = os.path.join(ASSETS, a["file"])
        if not os.path.exists(src):
            continue
        # name the output file after the real asset, e.g. MP3__CAHero_BadBoy.ogg
        real = names.get(str(a.get("index")))
        stem = ("MP3__" + os.path.basename(real)) if real else ("%06d" % i)
        stem = "".join(c if c.isalnum() or c in "_-." else "_" for c in stem)
        rel = "FxSound/%s.ogg" % stem
        shutil.copy(src, os.path.join(OUT, rel))
        out_assets.append({
            "id": "FxSound/%06d" % i, "archive": "FxSound", "index": i,
            "offset": a.get("offset", 0), "size": os.path.getsize(os.path.join(OUT, rel)),
            "format": "ogg", "mime": "audio/ogg",
            "name": real,                      # the real name, e.g. MP3/CAHero_BadBoy
            "file": rel, "confidence": "high",
        })

    # The UI sprites are plaintext BMPs already named by the game, so take them
    # straight from disk. The manifest's ui_sprites list is not relied on: the
    # index-decoded manifest describes the .idd payloads instead.
    sprites = []
    vh = os.path.join(ASSETS, "vh")
    if os.path.isdir(vh):
        for fn in sorted(os.listdir(vh)):
            if not fn.lower().endswith(".bmp"):
                continue
            src = os.path.join(vh, fn)
            rel = "vh/" + fn
            shutil.copy(src, os.path.join(OUT, rel))
            w = h = 0
            try:
                with open(src, "rb") as fh:
                    head = fh.read(32)
                w, h = struct.unpack_from("<ii", head, 18)
            except Exception:
                pass
            sprites.append({"name": os.path.splitext(fn)[0], "file": rel,
                            "width": w, "height": abs(h),
                            "size": os.path.getsize(src)})

    # named-asset catalog for the client's browse tab
    cat = os.path.join(ROOT, "work/catalog.json")
    if os.path.exists(cat):
        shutil.copy(cat, os.path.join(OUT, "catalog.json"))

    json.dump({
        "generated": man.get("generated", ""),
        "summary": {"total_assets": len(out_assets),
                    "by_format": {"ogg": len(out_assets)},
                    "by_archive": {"FxSound": len(out_assets)},
                    "ui_sprites": len(sprites), "ndadata_pak": 0},
        "archives": [{"name": "FxSound", "idd_size": 0,
                      "asset_count": len(out_assets)}],
        "assets": out_assets, "ui_sprites": sprites, "ndadata": [],
    }, open(os.path.join(OUT, "manifest.json"), "w"), separators=(",", ":"))

    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(OUT) for f in fs)
    print(f"songs  : {len(out_assets)}")
    print(f"sprites: {len(sprites)}")
    print(f"output : {OUT}  ({total/1_048_576:.1f} MB)")
    print("serve with: cd deploy && python3 -m http.server 8000")


if __name__ == "__main__":
    main()
