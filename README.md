# Boom → Web

Porting the **Club Audition / 오디션** (T3 Entertainment) Windows client in `Boom.zip`
to something usable on the web.

- **Source archive:** `Boom.zip` (558 MB → 1.30 GB extracted, 367 files)
- **Extracted to:** `extracted/Boom/`
- **Format research:** [`NOTES.md`](./NOTES.md) ← all reverse-engineering findings
- **Last updated:** 2026-10-28

---

## ⚠️ Read this first: what "port to web" can and cannot mean

**Can this become a playable game in the browser? No — not from this archive.**

| | Verdict | Why |
|---|---|---|
| **Asset browser / viewer** | ✅ **Feasible, underway** | Assets extract cleanly in places; a static web app needs no game logic. |
| **Playable game** | ❌ **Not feasible** | See the four blockers below. |
| **Data/string browser** | ✅ **Feasible, done** | 30 decoded containers incl. 10k+ Korean strings. |

Four hard blockers to a playable port:

1. **It's an online-only, server-authoritative MMO.** Rooms, matchmaking, scoring,
   item ownership and song sync all live on the *server*, which is **not in this
   archive**. There is no offline mode to port. Without the server there is no game
   to play, no matter how much of the client is reverse-engineered.
2. **The client code is protected.** `CA.exe` is packed with nProtect GameGuard /
   BlackCipher; `CA.dll` and `DWK.dll` are **encrypted on disk** (they are byte-identical
   to each other and contain no readable structure). The game logic is not directly
   readable.
3. **The asset container is only partly reversed.** Of 12 `.idd` archives, **1 is
   fully extractable**. The rest use a custom container we have not cracked yet.
4. **A renderer would have to be written from scratch.** DirectX 9, custom `.fft`
   fonts, `.idd` sprite/animation tables, Bink video (`.bik`). None of this maps to
   the browser; it would be a reimplementation, not a port.

**Realistic end state:** a web **asset & data browser** over everything extractable,
plus — if wanted later — a *new* rhythm minigame reusing extracted audio/art. That
would be an original game inspired by the assets, **not** a port of this one.

---

## Progress at a glance

| Phase | Status | Progress |
|---|---|---|
| 0. Extract archive | ✅ Done | 367 files / 1.30 GB |
| 1. Decode `ssi1` containers | ✅ Done | 30 files decoded |
| 2. `ndadata/*.pak` | ✅ Done | 68 inflated |
| 3. Extract `FxSound.idd` | ✅ Done | **693 Oggs, 100% coverage, verified** |
| 4. Copy UI sprites | ✅ Done | 34 BMPs, real names |
| 5. Build asset extractor | ✅ Done | `scripts/extract_assets.py` |
| 6. Generate manifest | ✅ Done | 693 assets + 34 sprites + 68 paks |
| 7. Web app UI | 🟡 In progress | data staged, **no HTML yet** |
| 8. Crack `.idx` filenames | 🟡 In progress | cipher not broken |
| 9. Remaining 11 `.idd` archives | 🔴 Blocked | need container format |
| 10. Game renderer / logic | ⬜ Not started | blocked by #9 + server |
| 11. Server protocol | ⬜ Not started | **likely infeasible** |

**Overall: the asset-extraction half is real and verified; the "playable game" half
is not achievable from this archive.** Roughly one of twelve asset archives is
fully recovered.

---

## TODO

### ✅ Done

- [x] **Unzip** `Boom.zip` → `extracted/Boom/`
- [x] **Solve `ssi1`/`ssi3` container** — 4-byte magic + raw zlib stream
- [x] **Decode all 30 `.ssd`/`.ini` containers** → `work/ssi/` (`*.bin` + `*.strings.txt`)
- [x] **Solve `ndadata/*.pak`** — `PACK0001` magic, zlib at offset 16 → inflates to the sibling `.idx`
- [x] **Inflate 68 `.pak` files** → `work/assets/ndadata/`
- [x] **Extract `FxSound.idd`** — 693 Oggs, verified 100% coverage, all decode
- [x] **Copy 34 `vh/*.bmp` UI sprites** (already have real names, no extraction needed)
- [x] **Build `scripts/extract_assets.py`** — magic detect + per-format length parsing
- [x] **Generate `work/assets/manifest.json`**
- [x] **Get REA MCP + Ghidra 12.1.4 working** — verified, 12,869 funcs decompiled

### 🟡 In progress

- [ ] **Web app UI** — data staged at `app/public/`, `sync.sh` written; `index.html`,
      router and views still missing. Routes planned: `/`, `#/textures`, `#/audio`,
      `#/sprites`, `#/data`
- [ ] **Crack the `.idx` cipher** → recover real filenames. Header is clear
      (`ca da ef XX`, version 15, two counts); body encrypted. Known-plaintext
      anchors exist (`.bmp` visible in cleartext; `?ameh`/`?onu1`/`?P3/.` repeated
      per archive ⇒ repeating key). Target: `Patcher.exe` via Ghidra

### 🔴 Blocked

- [ ] **Extract the remaining 11 `.idd` archives** (`FxMap` 90MB, `FxStage` 56MB,
      `FxCharacter` 33MB, `fx` 87MB, `CharTE` 289MB, `EmoTE` 225MB, …)
      **Blocker:** these are a *custom container*, not stored files. Entropy 6.0–7.4
      vs FxSound's uniform 7.95; apparent `BM`/`DDS`/JPEG hits are coincidental
      (e.g. `bfSize` = 1,292,292,165). Needs the container format reversed in
      `Patcher.exe` — same engine that reads `.idx`, so this is one job with the
      cipher work above.

### ⬜ Not started

- [ ] DDS texture decoding in-browser (DXT1/DXT5 → canvas)
- [ ] Sprite-sheet slicing (the `.idd` prologue looks like an animation/UV table)
- [ ] Font handling for the 5 `.fft` fonts
- [ ] Optional: standalone rhythm minigame reusing extracted audio/art
- [ ] Server protocol reverse-engineering — **likely infeasible**, see above

---

## Repository layout

```
Boom.zip                  source archive (558 MB)
extracted/Boom/           extracted client (1.30 GB) — READ ONLY
  CA.exe                  main client, nProtect-packed
  CA.dll / DWK.dll        byte-identical, encrypted on disk
  Patcher.exe             ★ 2.7 MB, UNPROTECTED — best RE target
  FxSound.idd (+.idx)     92 MB — the one fully-extracted archive
  vh/*.bmp                34 plaintext UI sprites
  ndadata/*.pak           compressed .idx bundles
NOTES.md                  all format findings + corrections
scripts/                  working tools (run with python3 -I)
  extract_assets.py       ★ the extractor
  decode_ssi.py           decode ssi1 containers
  idd_walk.py             raw payload magic walk
work/
  ssi/                    30 decoded data containers
  assets/                 extracted output + manifest.json
  idx/                    cipher-crack scratch
app/                      the web app (data staged; UI in progress)
```

## How to run

```bash
# Re-extract assets (idempotent)
python3 -I scripts/extract_assets.py --dry-run          # count only
python3 -I scripts/extract_assets.py --archive FxSound  # one archive
python3 -I scripts/extract_assets.py                    # all

# Decode the ssi1 data containers
python3 -I scripts/decode_ssi.py work/ssi

# Serve the web app (once the UI lands)
cd app/public && python3 -m http.server 8000
```

## Key findings (detail in `NOTES.md`)

- **`ssi1`/`ssi3`** = magic + raw zlib ⇒ clean key/value data tables.
- **`ndadata/*.pak`** = `PACK0001` + zlib@16 ⇒ exactly the sibling `.idx` bytes.
- **`.idx`** header clear (`ca da ef XX`, v15, 2 counts); **body encrypted**.
  Not zlib/bz2/lzma, not a fixed keystream (XOR of two archives = 7.46 bits/byte).
  ~40-byte records; name field then two equal u32s then a zero.
- **`.idd` is only sometimes a plain container.** `FxSound.idd` holds stored Oggs
  (100% recovered); most others are a custom container.
- **`CA.exe`/`CA.dll`/`DWK.dll` are protected.** `Patcher.exe` is not — use it.

## Verification standard

Counts here are only reported after **per-format validation and a coverage check**.
Two earlier claims were retracted for skipping that step:

1. "~23,877 Ogg streams in FxSound" — actually counted Ogg *page headers*; real
   count **693**. Verified by 100% byte coverage.
2. "FxMap/FxStage are BMP/DDS-heavy and magic-carveable" — those were coincidental
   byte matches; a strict validator rejects them.

Raw magic-hit counts are **not** asset counts. See `NOTES.md` §2 CORRECTION.
