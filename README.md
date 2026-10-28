# Boom → Web

Porting the **Club Audition / 오디션** (T3 Entertainment) Windows client in `Boom.zip`
to something usable on the web.

- **Source archive:** `Boom.zip` (558 MB → 1.30 GB extracted, 367 files)
- **Extracted to:** `extracted/Boom/`
- **Format research:** [`NOTES.md`](./NOTES.md) ← all reverse-engineering findings
- **Last updated:** 2026-10-28

---

## ⚠️ Read this first: what "port to web" can and cannot mean

**Can this become a playable game in the browser? A new one, yes — a port of the
original, no.**

| | Verdict | Why |
|---|---|---|
| **Asset browser / viewer** | ✅ **Done** | 5 routes, DDS decode, XSS-tested. |
| **Data/string browser** | ✅ **Done** | 30 decoded containers incl. 10k+ Korean strings. |
| **Playable rhythm game** | ✅ **Done** | Original game on the real assets — see [Playable game](#-playable-game). |
| **Port of the original game** | ❌ **Not feasible** | See the four blockers below. |
| **All assets extracted** | 🟡 **~12.6%** | Payload layout needs a protected binary. |

Four hard blockers to a *port*:

1. **It's an online-only, server-authoritative MMO.** Rooms, matchmaking, scoring,
   item ownership and song sync all live on the *server*, which is **not in this
   archive**. There is no offline mode to port. Without the server there is no game
   to play, no matter how much of the client is reverse-engineered.
2. **The client code is protected.** `CA.exe` is packed with nProtect GameGuard /
   BlackCipher; `CA.dll` and `DWK.dll` are **encrypted on disk** (they are byte-identical
   to each other and contain no readable structure). The game logic is not directly
   readable.
3. **The asset container is only partly reversed.** **~12.6% of the 1,086 MB of asset
   volume is recovered** — 1,801 entries. One archive (`FxSound`) is complete; the rest
   are partial or empty. The `.idx` cipher is cracked, but the payload layout lives in
   Themida-protected `CA.dll`.
4. **A renderer would have to be written from scratch.** DirectX 9, custom `.fft`
   fonts, `.idd` sprite/animation tables, Bink video (`.bik`). None of this maps to
   the browser; it would be a reimplementation, not a port.

**Delivered end state:** a web **asset & data browser** over everything extractable,
plus a **playable rhythm game** built on the extracted audio and art. That game is an
original work inspired by these assets, **not** a port of the original.

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
| 7. Playable game | ✅ Done | rhythm game, beat maps from audio, SELFTEST PASS |
| 8. Crack `.idx` cipher | ✅ Done | **379 real names, 128 verified** |
| 9. Name the big Fx* indexes | 🟡 In progress | cipher cracked, record walk pending |
| 10. Game renderer / logic | ⬜ Not started | blocked by #3 + server |
| 11. Server protocol | ⬜ Not started | **infeasible**, see below |

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

### Why the remaining ~87% is blocked

Two separate reasons, and only the second is hard:

**1. The `.idx` cipher is CRACKED** (see §8 of `NOTES.md`). Names use
`name[i] = stem[i] ^ name[i-4]`, with the 4-byte seed derived from the leading
directory. 379 real names recovered, 128 of them verified against plaintext found
independently in the bundles' compiled Lua. **No decompiler was needed** and none
would have helped — a decompiler yields code, not the known plaintext that solves
a cipher.

**2. The payload layout is still unknown, and this is the real wall.** The big
archives' contents are zlib-compressed custom structs rather than stored files, and
the index offset fields do **not** point at payload starts — verified: they land on
struct headers (`01 00 00 00 02 00 00 00`). FxStage, FxCharacter, FxContents and `fx`
contain **zero** valid zlib streams. Reading that layout requires the engine binary,
and **`CA.dll` is Themida-protected** (`.themida` section, 7,987,200 bytes virtual,
`rawsz=0`, plus UPX) while `CA.exe` is nProtect GameGuard-packed. Both defeat static
analysis.

`Patcher.exe` (2.7 MB, 12,869 functions) **is** analysable, but it is only a downloader —
no `.idd`, `.idx` or `pak` strings and none of the format code.

External corroboration: the Zenhax thread on this game family calls the encryption
*"custom (something like 256 different operations) and so it's useless to make a script
for quickbms."* Consistent with what is measured here.

**Remaining options, in order of promise:**
1. **Finish the big-index record walk.** The cipher already works on them — forcing
   `Game/` on `FxStage.idx` yields `Game/AIBattle_SuperSt…` — only the fixed-width
   record layout needs parsing. Cheapest real win available.
2. **Signature carving** — raises coverage archive by archive. Already got FxSound to
   100% and FxHiddenCatch to 38%.
3. **Find a community extractor.** This family has public unpackers (ACV tools,
   HyperRipper for the sibling `.idd`/`.idx`). Unknown: whether any handles *this*
   client's generation.
4. **Dynamic analysis** — dump decrypted code from a running client. Requires Windows
   with anti-cheat active; outside this repo's scope.

**Overall: the asset-extraction half is real and measurable, and a playable
asset-based game is DONE. A port of the original game remains impossible from this
archive.** ~12.6% of asset volume recovered.

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
- [x] **Build a playable game** — original rhythm game on the extracted assets,
      beat maps detected from each track's own audio, `?selftest=1` passes
- [x] **Crack the `.idx` name cipher** — self-differential stream,
      `name[i] = stem[i] ^ name[i-4]`, seed derived from the leading directory.
      **379 real names, 128 verified against the Lua plaintext.** No decompiler
      needed; `scripts/idx_decrypt.py`

### 🔴 Blocked

- [ ] **Extract the remaining ~87% of asset volume**
      (`CharTE` 289 MB, `EmoTE` 225 MB, `FxMap` 90 MB, `fx` 87 MB, …).
      **Blocker:** the payloads are zlib-compressed custom structs rather than
      stored files, and the index offset fields do **not** point at payload
      starts — verified: they land on struct headers (`01 00 00 00 02 00 00 00`).
      FxStage, FxCharacter, FxContents and `fx` contain **zero** valid zlib
      streams. Reading the real layout needs the engine binary, and `CA.dll` is
      Themida-protected while `CA.exe` is GameGuard-packed.

### 🟡 In progress

- [ ] **Name the big `Fx*` indexes.** The cipher is cracked and applies to them
      too — forcing `Game/` on `FxStage.idx` yields `Game/AIBattle_SuperSt…` —
      but those indexes use a **fixed-width** record layout instead of the
      ndadata length-prefixed one, so the record walk still needs writing.
      This would name the archives holding most of the remaining bytes.

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
- **`.idx` names: CRACKED.** Self-differential stream, `name[i] = stem[i] ^ name[i-4]`,
  with the 4-byte seed derived from the leading directory (`Game/`, `Quest/`,
  `PopupEvent/`). 379 real names, 128 verified against Lua plaintext. Two index
  families: `fc 01 b2 05` (length-prefixed, decoded) and `ca da ef` (fixed-width,
  walk pending).
- **`.idd` is only sometimes a plain container.** `FxSound.idd` holds stored Oggs
  (100% recovered); most others hold zlib-compressed custom structs whose index
  offsets point at struct *headers*, not payloads.
- **`CA.exe`/`CA.dll`/`DWK.dll` are protected** — Themida and GameGuard. `Patcher.exe`
  is analysable but holds no format code. **A decompiler was not needed for the
  cipher**, and none of these would have helped with it.

## Verification standard

Counts here are only reported after **per-format validation and a coverage check**.
Two earlier claims were retracted for skipping that step:

1. "~23,877 Ogg streams in FxSound" — actually counted Ogg *page headers*; real
   count **693**. Verified by 100% byte coverage.
2. "FxMap/FxStage are BMP/DDS-heavy and magic-carveable" — the *counts* came from
   coincidental byte matches, and a strict validator rejects those. Note the JPEGs
   that did validate are genuinely real (`JFIF standard 1.02`); it was the volume,
   not the format, that was wrong.

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

---

## Getting set up from a fresh clone

`main` carries source only. The extracted assets are generated, so build them first:

```bash
# 1. put Boom.zip in the repo root, then
python3 -I scripts/extract_assets.py    # -> work/assets + manifest  (~140 MB, a few minutes)
python3 -I scripts/build_deploy.py      # -> deploy/                 (the playable site)
python3 -I scripts/build_artifact.py    # -> one self-contained HTML file
python3 -I scripts/names_lua.py         # -> real UI names from the Lua bundles

cd deploy && python3 -m http.server 8000
```

Nothing under `work/assets/`, `deploy/` or `app/public/<Archive>/` is committed —
all of it regenerates from `Boom.zip`, which is why `.gitignore` lists it.
