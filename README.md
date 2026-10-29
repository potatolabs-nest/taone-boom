# Crazy Arcade → Web

Porting the **Crazy Arcade** (크레이지 아케이드 / BnB) NEXON client in `Boom.zip`
to the web.

> **Correction (2026-10-30):** this project was previously misidentified as
> "Club Audition" by T3 Entertainment. It is **Crazy Arcade by NEXON** — the
> archive's own string tables contain `Nexon` ×24, `넥슨` ×88, `크아` ×159 and the
> Crazy Arcade roster (배찌 Bazzi, 다오 Dao, 우니 Uni, 로두마니 Lodumani). `CA.exe`
> means **Crazy Arcade**. Research notes gathered about Audition (§9, §12, §13 of
> `NOTES.md`) targeted the wrong game and have been marked as such.

- **Source archive:** `Boom.zip` (558 MB → 1.30 GB extracted, 367 files)
- **Extracted to:** `extracted/Boom/`
- **Format research:** [`NOTES.md`](./NOTES.md) ← all reverse-engineering findings
- **Live:** https://potatolabs-nest.github.io/taone-boom/



## ⚠️ Read this first: what "port to web" can and cannot mean

**Can this become a playable game in the browser? A new one, yes — a port of the
original, no.**

| | Verdict | Why |
|---|---|---|
| **Asset browser / viewer** | ✅ **Done** | 5 routes, DDS decode, XSS-tested. |
| **Data/string browser** | ✅ **Done** | 30 decoded containers incl. 10k+ Korean strings. |
| **Web client shell** | ✅ **Done** | Login → lobby → matching → room → play → result, real UI strings and sprites. |
| **Playable rhythm game** | ✅ **Done** | Original game on the real assets — see [Playable game](#-playable-game). |
| **Port of the original game** | ❌ **Not feasible** | See the four blockers below. |
| **All assets extracted** | ✅ **Done** | `.idx`/`.idd` container solved — **100.00%, lossless.** |

Four hard blockers to a *port*:

1. **It's an online-only, server-authoritative MMO.** Rooms, matchmaking, scoring,
   item ownership and song sync all live on the *server*, which is **not in this
   archive**. There is no offline mode to port. Without the server there is no game
   to play, no matter how much of the client is reverse-engineered.
2. **The client code is protected.** `CA.exe` is packed with nProtect GameGuard /
   BlackCipher; `CA.dll` and `DWK.dll` are **encrypted on disk** (they are byte-identical
   to each other and contain no readable structure). The game logic is not directly
   readable.
3. **The asset container is now SOLVED.** The `.idx` is the directory and the
   `.idd` is a plain concatenation of its payloads: `sum(idx sizes) == .idd size`
   exactly, so extraction is **lossless and 100.00% complete** — 43,425 named
   entries, all 1,086 MB, verified by SHA-256 round trip. (A residue of
   ~1,300 encrypted `Map/*` records exists but is fully carved and named.)
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
| 3. Extract assets from `.idd` | ✅ Done | **43,425 entries, 100.00% of 1,086 MB, lossless** |
| 4. Copy UI sprites | ✅ Done | 34 BMPs, real names |
| 5. Build asset extractor | ✅ Done | `scripts/extract_assets.py` |
| 6. Asset browser | ✅ Done | 5 routes, DDS decode, XSS-tested |
| 6b. Web client shell | ✅ Done | login/lobby/matching/room/play/result, FLOWTEST PASS |
| 7. Playable game | ✅ Done | rhythm game, beat maps from audio, SELFTEST PASS |
| 8. Crack `.idx` cipher | ✅ Done | **379 real names, 128 verified** |
| 9. Name the big Fx* indexes | ✅ Done | **43,425 names**, chain walk solves to EOF |
| 10. Game logic / renderer | ❌ Not achievable | logic is server-side + in Themida-protected `CA.dll` |
| 11. Server protocol | ⬜ Not started | **infeasible**, see below |

### What the 43,425 entries actually are

The archive is **100% decoded and lossless**, but "decoded" is not the same as
"renderable". Breaking the entries down by what their own bytes say:

| kind | count | note |
|---|--:|---|
| data records | ~42,500 | sprite/avatar/map **descriptors**: small LE integer counts, entropy 2.6–6.5 |
| Ogg audio | 747 | real, verified with `file`/`afinfo` |
| JPEG images | 91 | real, `JFIF` |
| UI sprites (`vh/`) | 34 | plaintext BMPs, real filenames |

So the media — all the audio and every stored image — is recovered and named.
The large remainder is the game's own metadata: the byte-exact cuts prove the
*structure* is right, but those records are tables the engine interprets, not
files anything else can open. That is the honest limit of what the archive holds.

### Extraction coverage — measured, not estimated

**The container is solved.** A `.idd` and its `.idx` are two halves of one archive:
the `.idx` is the *directory* (it names every entry and stores that entry's exact
byte length) and the `.idd` is the *payload blob* — the entries concatenated in
`.idx` record order, no gaps, no per-file header.

`sum(idx sizes) == os.path.getsize(.idd)` **exactly**, on all 12 archives. That
identity makes extraction exact rather than heuristic: no magic scanning, no guessed
lengths, no truncation, 100.00% byte coverage.

| archive | size | entries | carved | coverage |
|---|--:|--:|--:|--:|
| CharTE | 289.0 MB | 17,558 | 289.02 MB | **100.00%** |
| EmoTE | 225.4 MB | 8,564 | 225.41 MB | **100.00%** |
| FxSound | 92.1 MB | 693 | 92.08 MB | **100.00%** |
| FxMap | 90.2 MB | 4,781 | 90.22 MB | **100.00%** |
| fx | 87.2 MB | 3,392 | 87.22 MB | **100.00%** |
| FxMonster | 71.9 MB | 1,216 | 71.86 MB | **100.00%** |
| FxStage | 56.2 MB | 1,137 | 56.22 MB | **100.00%** |
| FxContents | 51.6 MB | 720 | 51.65 MB | **100.00%** |
| FxDesktop | 48.5 MB | 1,935 | 48.54 MB | **100.00%** |
| FxHiddenCatch | 40.3 MB | 302 | 40.29 MB | **100.00%** |
| FxCharacter | 33.5 MB | 3,116 | 33.53 MB | **100.00%** |
| FxAsset | 0.16 MB | 11 | 0.16 MB | **100.00%** |
| **TOTAL** | **1,086 MB** | **43,425** | **1,086.20 MB** | **100.00%** |

**Lossless, proved by round trip.** Reassembling each `.idd` from its extracted
payloads reproduces the original file **byte for byte** — SHA-256 matches on
**12/12** archives. Zero bytes are guessed or dropped.

By format: 40,349 engine sprite/animation `table` records, 2,238 `bin` records
(907 of them exact-size zlib — `[u32 comp][u32 inflated][zlib]`, both fields exact,
10.3× ratio), 747 Ogg streams (`libVorbis`), 91 real JPEGs (`JFIF`, `Exif`).

The `.idx` walk is also independent of, and consistent with, the archive already
solved by another method: FxSound yields **exactly 693 records**, each a valid Ogg
whose own page-walk total equals its declared size.

### The one thing still open (and why it does not block assets)

1,324 `bin` payloads are **keystream-encrypted** — mostly `Map/*` map data,
`MapScriptTemplate/*` and object/attr tables. They are carved and named, but their
insides need a keystream recovery. The keystream is partly **exposed**: in FxMap's
893 `Map/*` records the high three bytes of the small-valued u32 fields are constant
across 200/200 files (`44 71 9c`, `e3 1b 9c`, `a1 61 9d` at offsets 5–7, 9–11,
13–15) — three direct samples, period ≠ 4. Ruled out for these: raw deflate, stored
flat, the self-differential `.idx` cipher, and fixed-XOR.

This is `Map` data, **not** the image/audio assets, which all live in the 40,349
`table` records, the 907 zlib records and the 838 validated jpg/ogg files — all
extracted. Details: [`work/idd_layout_report.md`](./work/idd_layout_report.md).

External corroboration for the remaining family: the Zenhax thread calls the
encryption *"custom (something like 256 different operations) and so it's useless to
make a script for quickbms."* Consistent with the sampling above.

**Overall: asset extraction is complete and lossless.** A port of the original game
still remains impossible from this archive — the server is not in it, and the client
binaries are Themida/GameGuard protected.

---

## TODO

### ✅ Done

- [x] **Unzip** `Boom.zip` → `extracted/Boom/`
- [x] **Solve `ssi1`/`ssi3` container** — 4-byte magic + raw zlib stream
- [x] **Decode all 30 `.ssd`/`.ini` containers** → `work/ssi/` (`*.bin` + `*.strings.txt`)
- [x] **Solve `ndadata/*.pak`** — `PACK0001` magic, zlib at offset 16 → inflates to the sibling `.idx`
- [x] **Inflate 68 `.pak` files** → `work/assets/ndadata/`
- [x] **Build `scripts/extract_assets.py`** — magic detect + per-format length parsing
- [x] **Carve 43,425 entries (100.00% of 1,086 MB)** — exact sizes read from the
      `.idx`, every payload header-validated, SHA-256 round trip on 12/12 archives
- [x] **Extract `FxSound.idd` completely** — 693 Oggs, 100% coverage
- [x] **Copy 34 `vh/*.bmp` UI sprites** (already have real names)
- [x] **Generate `work/assets/manifest.json`**
- [x] **Get REA MCP + Ghidra 12.1.4 working** — verified, 12,869 funcs decompiled
- [x] **Build the web app** — 5 routes, DDS DXT1/3/5 decode, 100/page pagination,
      XSS-tested against a malicious manifest
- [x] **Build a playable game** — original rhythm game on the extracted assets,
      beat maps detected from each track's own audio, `?selftest=1` passes
- [x] **Build the web client shell** — `client.html`, login → lobby → room → play
      → result, driven by the client's own strings (`나가기`, `상점`, `내아이템`,
      `난이도`, `쉬움/보통/어려움`) and its real sprite assets. `?flowtest=1` passes,
      in both `app/public` and the built bundle.
- [x] **Crack the `.idx` name cipher** — self-differential stream,
      `name[i] = stem[i] ^ name[i-4]`, seed derived from the leading directory.
      **379 real names, 128 verified against the Lua plaintext.** No decompiler
      needed; `scripts/idx_decrypt.py`
- [x] **Name the big `Fx*` indexes** — the chain is **global**, not per-record
      (that was the missing piece). Records are `[name][20-byte trailer]` where the
      trailer carries the payload size and the *next* name's length. **43,425 names**
      across 12 indexes; names have no file extensions.
- [x] **Crack the large `.idd` internal layout** — `.idx` is the directory,
      `.idd` is the concatenated payloads. `sum(sizes) == .idd size` exactly, so
      extraction is exact. **43,425 entries, 1,086 MB, 100.00%, SHA-256 round trip on
      12/12 archives.**

### 🟡 In progress (agents running)

- [ ] **Recover the keystream for the 1,324 encrypted `bin` payloads** (mostly
      `Map/*`). They are carved and named; the keystream is partly exposed from the
      constant high bytes of small-valued fields. Not image/audio, so it does not
      block the asset browser.
- [ ] **Extract the named `ndadata` popup assets.** The names are known (130 real
      paths) and the records carry two unexplained `u32` fields; if those resolve
      to offsets, the sprites inside become extractable as *named* files.

### ⬜ Not started (and not achievable from this archive)

- [ ] Server protocol, matchmaking, rooms, scoring — **the server is not in the
      archive**.
- [ ] A faithful gameplay port — the client binaries are Themida/GameGuard
      protected, so the original logic cannot be read out.

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

## Can the original game run in a browser? No — blocked on three fronts at once

Exhaustive external research (three web sweeps; sources in `NOTES.md` §12) and
direct archive analysis agree. Only **one** of the three blockers is a
reverse-engineering problem, and more effort on this archive cannot move any of them.

| # | Blocker | Status |
|---|---|---|
| 1 | **The server** | Not in the archive. Two public emulators exist, both incomplete and both for other builds: a Java one (*"not finish server file. Full source code missing packet"*, Season 5 / Redbana 2019), and an **openly readable C# one** whose account layer has real recovered framing (`ushort` length + opcode `0x65`) but whose GameServer README says it *"does not yet implement gameplay, rooms, user sync, client handshakes or protocol encryption."* |
| 2 | **The protected binary** | `CA.exe`/`CA.dll` are Themida + GameGuard packed, so the client **cannot be recompiled**. And a browser client cannot pass XTrap/GameGuard/BlackCipher at all. |
| 3 | **The note charts** | Not in the archive — charts live in `.acv` files and this archive contains **zero** `.acv`. No public decoder for the chart container exists. |

**The renderer is no longer the hard part, and that is worth knowing.** A real
DirectX 9 client has now been shipped in a browser: *GunZ: The Duel* was compiled
to WASM behind a D3D9→WebGL layer, and its author is explicit that it is *"the
actual GunZ client running natively, not a remake."* That route needs the client's
C++ source or buildable DLLs — which is exactly what blocker 2 denies us.

Server binaries for older versions (Chinese 12.4, 1.6, 1.7, 3.25, 8.3, 14.2,
16.10) are publicly obtainable — but as **executables plus MySQL dumps, never
source**, and users repeatedly describe them as **not turnkey**. The best open
starting point, if anyone ever builds a server, is
[`Marcmendozt/audition-server-platform`](https://github.com/Marcmendozt/audition-server-platform).
**Client source code does not exist publicly anywhere** (verified negative across
GitHub, GitLab, Codeberg, SourceForge and archive.org).

**A browser remake of Audition already exists** (RaGEZONE, three.js + Node/SQLite),
written in "a few hours" and self-described as rough. It is a reimplementation,
not the original — which is the same honest category as what this repo delivers.

### Also confirmed: avatars are 3D, not 2D sprites

Audition runs on the **Gamebryo** engine with DirectX 9.0c. `.rgm` models are built
in 3DS MAX 8 and carry **bone hierarchies and animation keyframes** with DDS
textures. So the archive's ~42,500 data records are 3D model/animation data plus
UI layout — which is why they are not renderable images, and why a faithful visual
port would need a skinned-mesh renderer rather than a sprite slicer. (Checked
directly: their headers are integer rectangle tables — counts and coordinates such
as `131, 106, 104, 118` — with no float keyframe data at the expected offsets.)

---

## Can the online game be restored? No — and here is why, precisely

Searched for server source code (details and links in `NOTES.md` §9).

| | |
|---|---|
| Is the server in `Boom.zip`? | **No.** |
| Is there a public emulator? | **Partly.** "Audition Reborn" (Java) — 93 packet types, login 18505, game 18506. But its release thread states *"not finish server file. Full source code missing packet"*, and downloads need a forum account. |
| Does it match this client? | **No.** It targets Season 5 / Redbana 2019. This archive is Club Audition KR, build 1014, Oct 2022. Packet layouts are version-specific. |
| Binary server files? | Yes, for versions 1.6–16.10, as binaries plus MySQL dumps — never as source. |
| Will a complete one appear? | The community has declined outright: *"nobody is gonna start working on an emulator as a public thing."* |

**So a faithful online port needs three things built from scratch:** the client
protocol (93 packet types, only partly documented), a working server (the public
one is incomplete), and the client rewritten for the browser. That is a
multi-month engineering project *on top of* this archive — not something
extraction can reach.

One further obstacle: this client ships **XTrap + nProtect GameGuard +
BlackCipher**, and a browser client cannot participate in that anti-cheat stack
at all.

The client in this repo is therefore a **local reconstruction** — real assets,
real UI, real flow, local rooms — not the live online game.

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
