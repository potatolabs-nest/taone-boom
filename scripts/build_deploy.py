#!/usr/bin/env python3
"""Build the static site deployed to GitHub Pages.

Produces ./deploy : the game plus a curated, size-bounded slice of the real
extracted assets (a spread of songs and the menu sprites). Everything it
writes is regenerable from Boom.zip, so ./deploy is not committed.

Usage: python3 -I build_deploy.py
"""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_GAME = os.path.join(ROOT, "app/public/game.html")
ASSETS = os.path.join(ROOT, "work/assets")
MANIFEST = os.path.join(ASSETS, "manifest.json")
OUT = os.path.join(ROOT, "deploy")

N_SONGS = 16


def main():
    if not os.path.exists(MANIFEST):
        sys.exit("run scripts/extract_assets.py first — no manifest at " + MANIFEST)
    man = json.load(open(MANIFEST))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "FxSound"))
    os.makedirs(os.path.join(OUT, "vh"))

    shutil.copy(SRC_GAME, os.path.join(OUT, "index.html"))
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

    out_assets = []
    for i, a in enumerate(picked):
        src = os.path.join(ASSETS, a["file"])
        if not os.path.exists(src):
            continue
        rel = "FxSound/%06d.ogg" % i
        shutil.copy(src, os.path.join(OUT, rel))
        out_assets.append({
            "id": "FxSound/%06d" % i, "archive": "FxSound", "index": i,
            "offset": a.get("offset", 0), "size": os.path.getsize(os.path.join(OUT, rel)),
            "format": "ogg", "mime": "audio/ogg", "name": None,
            "file": rel, "confidence": "high",
        })

    sprites = []
    for s in man.get("ui_sprites", []):
        src = os.path.join(ASSETS, s["file"])
        if not os.path.exists(src):
            continue
        rel = "vh/" + os.path.basename(s["file"])
        shutil.copy(src, os.path.join(OUT, rel))
        sprites.append({"name": s.get("name"), "file": rel,
                        "width": s.get("width", 0), "height": s.get("height", 0),
                        "size": os.path.getsize(os.path.join(OUT, rel))})

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
