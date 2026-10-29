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

## Progress at a glance  (updated 2026-10-30)

| Area | State | Detail |
|---|---|---|
| Archive decode | ✅ **100%** | 43,425 entries, 1,086 MB, lossless, SHA-256 round-trip verified |
| `.idx` name cipher | ✅ Solved | 379 + 43,425 names; verified against independent plaintext |
| `.table` record header | ✅ Solved | `24 + 48*count`, holds on 40,349/40,349 |
| Media extraction | ✅ Done | 747 Ogg songs, 91 JPEG, 34 UI sprite sheets, 180 event-art images |
| **Game screenshots found** | ✅ **139 real in-game captures** | actual Crazy Arcade gameplay, HUD and item panel |
| Web UI (Crazy Arcade look) | 🟡 **In progress** | glossy CA panels + sampled palette in; sprite-sheet frames being fixed |
| Playable game | 🟡 In progress | rhythm mode works; **building the real maze/bomb stage** |
| Sprite pixel codec | ❌ Not cracked | ~3.2 B/px proprietary codec; no public implementation exists anywhere |
| Engine logic | ❌ Not reachable | Themida-encrypted `CA.dll` (`rawsz=0` section, EP in `.boot`) |
| Server | 🟡 **Lead found** | `PinguBNB` (C#) — working, documented protocol, **but no KR locale** |
| Game charts | ❌ Absent | archive contains no `.acv`; charts aren't here |

### What changed most recently
1. **Game identity corrected** — this is *Crazy Arcade* (크레이지 아케이드 / BnB, NEXON),
   not Audition. The archive's own strings prove it (`Nexon` ×24, `크아` ×159,
   Bazzi/Dao/Uni/Lodumani, `Crazy Arcade BnB`).
2. **139 real in-game screenshots recovered** from the quest bundles — actual
   gameplay, the item panel (speed / bomb / range), HUD and map tiles.
3. **UI rebuilt to the game's own design language** — palette sampled from the
   sprites (`#09cdff` panel, `#026fc5` frame, `#3d00d8` accent), glossy beveled
   panels and buttons, real sprite-sheet frames for mode buttons.
4. **English + Vietnamese UI** with a language switcher, keyed by the original
   Korean so nothing is lost.
5. **A real server exists**: `PinguBNB` (C#, .NET 10) with documented framing —
   TCP 3838/4848/4849, UDP 3839/4849, region cipher-degree model, opcode YAML.
   It has **no KR locale**, which is the concrete gap for this client.

### Honest blockers
- **Sprite codec**: ~40,000 sprite payloads are a proprietary ~3.2 bytes/pixel
  codec. Verified absent from public sources in six languages. The decoder lives
  in Themida-encrypted `CA.dll`. *Workaround*: the 139 real screenshots supply the
  art directly.
- **KR opcode table**: PinguBNB covers JP/TW/CN/TH/VN/NA only.
- **Charts**: not in this archive.

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

## What public material exists for Crazy Arcade

Research now targets the **right game** (an earlier pass mistakenly researched
Audition by T3 Entertainment — see the correction at the top).

### Our `.idd`/`.idx` work appears to be the first public parse
The one on-point public request is an **unanswered** Spriters Resource thread
(Dec 2024): HyperRipper *"rips UI graphics and nearly every MP3/sound file"* but
*"character/enemy/map sprites … are missing, plus HR doesn't work with .idx files"*.
That matches exactly what we measured — signature scanning works, `.idx` directory
parsing is what nobody had.

An adjacent C# implementation, **Idx-Poptag-GUI**, cross-validates our format:
`CharTE` uses KeyTag `bvat` with header 47 / record 55; `EmoTE` uses `ghar` with
header 48 / record 56; records carry an `IddOffset` into the `.idd`. It has **no
sprite pixel decoder**.

### A working server exists publicly — and it is Python
[RaGEZONE thread, Aug 2026](https://forum.ragezone.com/threads/an-handmade-crazy-arcade-server-program.1270621/).
The author states: *"server was made by Python … NO database — only run the python
file and login program and login with an fake account to play. no score saved and
all maps can play. client has been embedded."* Ships `Crazy Arcade.7z` (9.8 MB).

Also sourced: **port `8798`**, from a 2008 Shanda 泡泡堂 server `system.ini`.

**No open server *source* exists** — every GitHub "CrazyArcade server" repo is a
from-scratch remake, not an emulator. The 单机版 ("standalone") builds circulating
are old leaked servers plus a patched client.

### The sprite codec is uncracked publicly
Confirmed negative across English, Korean, Chinese, Taiwanese, Vietnamese and
Indonesian sources — nobody has published even a failed attempt. The community
works around it by **redistributing the original `Pic/*.bmp` art** (5,474-image
library on 爱给网; a fan remake whose `Pic/` holds a near-complete bitmap set).

### ⭐ A real open-source server exists: PinguBNB
[`york8817612/PinguBNB`](https://github.com/york8817612/PinguBNB) — C# / .NET 10
**BNB game server emulator**, verified by fetching it. Wire protocol is documented:

- Listens on **TCP 3838/4848/4849, UDP 3839/4849**
- Region-dependent framing via a "cipher degree" (1 = JP/TW, 2 = CN, 3 = TH/VN/NA),
  controlling header length, opcode width and CRC (CRC32 vs CRC8)
- Header byte = `(0 + 231) ^ (192 + seq)`; length fields XOR-masked with `0xA569`
  or `0x96CA5395`; payload is an XOR stream keyed on packet sequence
- Opcodes in per-locale YAML: `LoginReq: 3`, `CreateSessionReq: 80`,
  `JoinSessionReq: 81`, `StartGameReq: 106`, `BombIgniteReq: 140`, …

**The gap:** it has **no KR locale**, and our client is Korean build 1014 (Oct 2022).
So it won't drive this client as-is — but it is a working skeleton whose cipher
model we can follow, and adding a KR opcode table is concrete work rather than
speculation.

*Caveat:* no LICENSE, no README, reverse-engineered tables. Reference material,
not something to redistribute.

### The one thing that would finish this
The **Python server + embedded client** bundle is the most promising path to a
genuinely playable Crazy Arcade — more so than anything found for the `.idd`
codec. It needs a free RaGEZONE account to download.

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
