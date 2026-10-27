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
3. **The asset container is only partly reversed.** **~12% of the 1,086 MB of asset
   volume is recovered** — 894 validated files. One archive (`FxSound`) is complete;
   the rest are partial or empty. The archive reader is in Themida-protected `CA.dll`.
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
| 3. Extract assets from `.idd` | 🟡 Partial | **1,801 entries, 12.64% of 1,086 MB** |
| 4. Copy UI sprites | ✅ Done | 34 BMPs, real names |
| 5. Build asset extractor | ✅ Done | `scripts/extract_assets.py` |
| 6. Web app | ✅ Done | 5 routes, DDS decode, XSS-tested |
| 7. Crack `.idx` filenames | 🔴 Blocked | engine binary is protected |
| 8. Game renderer / logic | ⬜ Not started | blocked by #7 + server |
| 9. Server protocol | ⬜ Not started | **infeasible**, see below |

### Extraction coverage — measured, not estimated

Two carving strategies, both format-validated:
- **Raw payloads** — files stored uncompressed, detected by magic with lengths parsed
  from each format's own header.
- **zlib streams** — entries stored as zlib-compressed records (`FxMap` has 893;
  `FxDesktop` 14). Each is carved and inflated; 200/200 sampled inflate cleanly at an
  8.26× ratio.

| archive | size | entries | carved | coverage |
|---|--:|--:|--:|--:|
| **FxSound** | 92.1 MB | 693 | 92.08 MB | **100.00%** |
| FxHiddenCatch | 40.3 MB | 24 | 15.44 MB | 38.32% |
| FxMap | 90.2 MB | 908 | 13.40 MB | 14.85% |
| FxContents | 51.6 MB | 21 | 4.49 MB | 8.69% |
| FxDesktop | 48.5 MB | 38 | 4.08 MB | 8.41% |
| FxStage | 56.2 MB | 18 | 3.55 MB | 6.32% |
| EmoTE | 225.4 MB | 62 | 3.75 MB | 1.66% |
| fx | 87.2 MB | 22 | 0.23 MB | 0.27% |
| FxMonster | 71.9 MB | 3 | 0.09 MB | 0.13% |
| CharTE | 289.0 MB | 12 | 0.23 MB | 0.08% |
| FxCharacter | 33.5 MB | 0 | 0.00 MB | 0.00% |
| **TOTAL** | **1,086 MB** | **1,801** | **137 MB** | **12.64%** |

By format: 747 Ogg streams (`libVorbis`, decode in `afinfo`), 147 JPEGs
(`JFIF standard 1.02`), 251 zlib-wrapped BMP, 656 zlib-wrapped binary records.

**So: ~12.6% of the asset volume is recovered.** One archive is complete; the rest are
partial. FxMap and FxHiddenCatch are the next-most-promising — both have substantial
compressed content still uncarved.

### Why the remaining 88% is blocked

The archive reader lives in **`CA.dll`, which is Themida-protected** — it has a literal
`.themida` section (7,987,200 bytes virtual, `rawsz=0`) plus a `.boot` section, and also
carries UPX. `CA.exe` is nProtect GameGuard-packed (entropy ~7.96). Themida and
GameGuard both defeat Ghidra's static analysis, so the container format and the `.idx`
cipher cannot be read out of the binary.

`Patcher.exe` (2.7 MB, 12,869 functions) **is** analysable, but it is only a downloader —
it contains no `.idd`, `.idx` or `pak` strings and none of the format code.

External corroboration: the Zenhax thread on this game family states the encryption is
*"custom (something like 256 different operations) and so it's useless to make a script
for quickbms."* Consistent with what is measured here.

**Remaining options, in order of promise:**
1. **Signature carving** (current approach) — raises coverage archive by archive. It
   already got FxSound to 100% and FxHiddenCatch to 38%.
2. **Find a community extractor.** This game family has public unpackers
   (ACV tools, HyperRipper for the sibling `.idd`/`.idx`). Unknown: whether any handles
   *this* client's generation.
3. **Dynamic analysis** — dump decrypted code from a running client. Requires running
   the game on Windows with anti-cheat active; outside this repo's scope.

**Overall: the asset-extraction half is real and measurable; the "playable game" half
is not achievable from this archive.** ~12% of asset volume recovered.

---

## TODO

### ✅ Done

- [x] **Unzip** `Boom.zip` → `extracted/Boom/`
- [x] **Solve `ssi1`/`ssi3` container** — 4-byte magic + raw zlib stream
- [x] **Decode all 30 `.ssd`/`.ini` containers** → `work/ssi/` (`*.bin` + `*.strings.txt`)
- [x] **Solve `ndadata/*.pak`** — `PACK0001` magic, zlib at offset 16 → inflates to the sibling `.idx`
- [x] **Inflate 68 `.pak` files** → `work/assets/ndadata/`
- [x] **Build `scripts/extract_assets.py`** — magic detect + per-format length parsing
- [x] **Carve 1,801 entries (12.64% of 1,086 MB)** — 747 Oggs + 147 JPEGs raw, plus 907 zlib streams
- [x] **Extract `FxSound.idd` completely** — 693 Oggs, 100% coverage
- [x] **Copy 34 `vh/*.bmp` UI sprites** (already have real names)
- [x] **Generate `work/assets/manifest.json`**
- [x] **Get REA MCP + Ghidra 12.1.4 working** — verified, 12,869 funcs decompiled
- [x] **Build the web app** — 5 routes, DDS DXT1/3/5 decode, 100/page pagination,
      XSS-tested against a malicious manifest

### 🔴 Blocked

- [ ] **Crack the `.idx` cipher** → recover the 1,801 entries' real filenames.
      **Blocker:** the reader is in `CA.dll`, which is **Themida-protected**
      (`.themida` section, `rawsz=0`, plus UPX); `CA.exe` is GameGuard-packed.
      `Patcher.exe` is analysable but contains no format code (it's a downloader).
- [ ] **Extract the remaining 88% of asset volume**
      (`CharTE` 289 MB, `EmoTE` 225 MB, `FxMap` 90 MB, `fx` 87 MB, …)
      **Blocker:** same protected engine. Currently only reachable by signature
      carving, which yields partial coverage per archive.

### ⬜ Not started

- [ ] Sprite-sheet slicing (the `.idd` prologue looks like an animation/UV table)
- [ ] Font handling for the 5 `.fft` fonts
- [ ] Optional: standalone rhythm minigame reusing extracted audio/art
- [ ] Server protocol reverse-engineering — **infeasible**, see above
- [ ] Decide whether 89 MB of extracted Oggs should stay in git (currently tracked;
      they are regenerable via `scripts/extract_assets.py`)

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

---

## ▶ Playable game

`app/public/game.html` is an **original browser rhythm game** built on the real
extracted assets — 693 songs and 34 UI sprites feed it, and beat maps are detected
from each track's own audio.

**To play it locally right now:**

```bash
python3 -I scripts/build_deploy.py     # builds ./deploy
cd deploy && python3 -m http.server 8000
# open http://localhost:8000/
```

Controls: `←` `↓` `↑` `→` hit the arrows · `Space` pause · `Esc` quit to lobby.
There is also an on-screen pad for touch devices. Add `?selftest=1` to the URL to
run the built-in smoke test of the detection and judging logic.

### Sharing it

The `gh-pages` branch already carries a self-contained build (16 songs, 34 sprites,
~10 MB), so the site is ready to serve — it only needs Pages switched on:

> **Repo → Settings → Pages → Source: Deploy from a branch → Branch: `gh-pages` / `(root)` → Save**

That gives `https://potatolabs-nest.github.io/taone-boom/`.

One catch: **Pages on a private repo needs GitHub Pro.** The repo currently returns
404 publicly, so either make it public or enable Pages on a paid plan.

### What the game is and is not

It **is** a real, playable rhythm game using unmodified assets from the shipped client.
It is **not** a port of Club Audition: the original is an online, server-authoritative
MMO whose server is not in this archive, and its client binaries are Themida/GameGuard
protected. See the four blockers above. Treat this as a new game built on rescued art
and audio, not a reconstruction of the original.

### Also published as a single HTML file

`scripts/build_artifact.py` inlines ten songs and twelve sprites into one ~6.8 MB
HTML file (`app/artifact/audition-web.html`) for hosts that take a single page rather
than a directory.
