# `.idd` / `.idx` internal layout — SOLVED

**Status: the container is cracked. 100.00% byte coverage of all 1,086 MB of
asset volume, exact sizes, real names — up from 12.6%.**

Verified two independent ways, one of them against pre-existing ground truth.

---

## 1. What the container is

A `.idd` and its sibling `.idx` are two halves of **one archive**:

- the **`.idx` is the directory** — it names every entry and stores the *exact*
  byte length of that entry's payload;
- the **`.idd` is the payload blob** — the entries are concatenated in `.idx`
  record order, with **no gaps and no per-file header**.

`sum(payload sizes) == os.path.getsize(.idd)` **exactly**, on all 12 archives.
That identity is what makes extraction exact rather than heuristic: no magic
scanning, no guessed lengths, no truncation, and full byte coverage.

```
archive          records      sum(sizes)          .idd size   ratio
FxAsset               11         155,592            155,592   1.00000
FxStage            1,137      56,224,755         56,224,755   1.00000
FxCharacter        3,116      33,532,812         33,532,812   1.00000
FxContents           720      51,646,646         51,646,646   1.00000
FxDesktop          1,935      48,538,009         48,538,009   1.00000
FxHiddenCatch        302      40,293,181         40,293,181   1.00000
FxMonster          1,216      71,864,820         71,864,820   1.00000
FxSound              693      92,079,817         92,079,817   1.00000
FxMap              4,781      90,223,416         90,223,416   1.00000
fx                 3,392      87,215,213         87,215,213   1.00000
CharTE            17,558     289,015,875        289,015,875   1.00000
EmoTE              8,564     225,405,063        225,405,063   1.00000
TOTAL             43,425   1,086,195,199      1,086,195,199   1.00000
```

## 2. The `.idx` cipher — the chain is GLOBAL, not per-record

NOTES.md §8 recorded the transform `name[i] = stem[i] ^ name[i-4]` but modelled it
as *per-name*. It is actually **one continuous chain over the whole body**, which
is why the record walk never previously lined up:

```
plain[i] = raw[i] ^ plain[i-4]      for i >= 4, across the whole body
plain[0:4] = raw[0:4] ^ seed
```

The body starts at offset **0x10**, after
`u32 magic | u32 version=15 | u32 count_a | u32 count_b`.

Measured on **every** archive: `plain[1:4] == raw[1:4]`, i.e. `seed == (k,0,0,0)`.
**Only the very first plaintext byte is masked**, by a single unknown byte `k`,
recovered by requiring the record chain to walk cleanly to EOF. It is *solved*,
not guessed, and no directory prefix has to be known. (`k` is also
`count_a & 0xFF` on several archives — a useful cross-check.)

## 3. Record layout

```
u32 magic | u32 version=15 | u32 count_a | u32 count_b
body: [name: L bytes][trailer: 20 bytes] [name][trailer] ...
```

```
trailer = u32 hash | u32 size | u32 zero | u32 zero | u32 L_next
```

- `L_next` is the **name length of the next record**; next record at `p + L + 20`.
- The **first** record's `L` is not stored — it is the leading run of path chars.
- The **final** record carries a **16-byte trailer** (no `L_next`); it is flushed
  when fewer than 20 bytes remain. (This is what made the walk stop one record
  short until fixed — and it is exactly why FxSound first yielded 692 then 693.)
- `size` is the exact payload size in the `.idd`. **This is the load-bearing field.**
- `count_a`/`count_b` in the header are *claims*, not the truth: the actual count
  is `records + (hdr count - DIFF)` where the DIFF is constant per archive
  (e.g. FxSound 698 → 693, FxMap 4770 → 4781). Walk the chain; do not trust the header.

## 4. Names have NO file extension

They are **asset group names**:

```
Bonus/Airplane1            MP3/Aliens
Game/AIBattle_SuperStar    HiddenCatch/Bt_close
Monster/AquaMon00_Blink    Tutorial/Tutorialback
Tile39/Waterway_LTile06    WhiteAngel/ChatWindow_Left
AvatarDeco/A02_10_0001_0LayerAdjust
Character/C00-EmotionA000LayerAdjust
```

**This is why every earlier scan failed**: they all required a known extension
(`.bmp/.dds/.ogg/...`) and therefore rejected 100% of real records.

## 5. Verification against independent ground truth

Two independent confirmations, one of them non-circular.

### (a) FxSound — against the archive already solved by another method

`FxSound.idd` had *already* been solved by an unrelated method (magic-carving →
693 contiguous Ogg streams, 100% coverage). Carving FxSound **purely from the
recovered `.idx` sizes**:

- yields **exactly 693 records** — the same number, independently derived;
- every one is a **valid standalone Ogg**;
- each Ogg's own page-walk total **equals the declared size exactly**;
- contiguous from offset 0 through EOF.

The full extraction also yields **exactly 747 `.ogg` payloads** across all
archives — the same 747 the README reached by magic-carving 693 + 54 elsewhere.

### (b) Lossless round trip — the strongest check

Reassembling each `.idd` from its extracted payloads, in index order, and
hashing it reproduces the original file **byte for byte**:

```
archive         reassembled      original   sha256
CharTE          289,015,875   289,015,875   match
EmoTE           225,405,063   225,405,063   match
FxAsset             155,592       155,592   match
FxCharacter      33,532,812    33,532,812   match
FxContents       51,646,646    51,646,646   match
FxDesktop        48,538,009    48,538,009   match
FxHiddenCatch    40,293,181    40,293,181   match
FxMap            90,223,416    90,223,416   match
FxMonster        71,864,820    71,864,820   match
FxSound          92,079,817    92,079,817   match
FxStage          56,224,755    56,224,755   match
fx               87,215,213    87,215,213   match
```

12/12 archives reproduce their original SHA-256. Extraction is **lossless and
complete**, so this is 100.00% coverage in the strongest available sense — zero
bytes are guessed or dropped.

## 6. What the payloads *are* (and are not)

All 43,425 payloads are extracted with **exact** sizes. Classifying them by
parsing their own headers gives three well-defined kinds plus one open one:

| kind | count | what it is |
|---|--:|---|
| `table` | 40,349 | engine sprite/animation tables (see below) |
| `bin` | 2,238 | 8-byte header + payload; three sub-kinds below |
| `jpg` | 91 | real JPEGs (JFIF/Exif, validated) |
| `ogg` | 747 | real Ogg/Vorbis streams (validated) |

**`table` (40,349).** Opens with the same header form as the whole `.idd`:
`u32 count | u32 2` — and `u32[1] == 2` holds on **40,349/40,349**, with
`u32[0]` always a small count (max 480). Then a rectangle, `0xFFFFFFFF`
sentinels, and u16-pair sequences. Per-64KB entropy 5.7–6.5, i.e. structured
table data, **not** compressed (compressed would be ~8.0). These are the
animation/sprite-atlas records. So the structure is **recursive**: the `.idd` is
a payload of payloads, and NOTES.md §2's "descriptor/animation table (u16
pairs)" was describing the *inside of a payload*, not the `.idd` header.

**`bin` (2,238)** splits further by what sits at offset 8:

- **907 are `[u32 compressed_len][u32 inflated_len][zlib stream@8]`.** Both
  fields are **exact**: `u32[0] == filesize-8` on 907/907 and
  `u32[1] == inflated length` on 907/907 (mean ratio 10.3×). This is the same
  record form the README already found in FxMap/FxDesktop — here it is placed
  correctly, with names.
- **7 are plain text** (`StageCredit/Credit` is literally readable).
- **1,324 are high-entropy (7.6–7.9) and are still encrypted** — see §6b.

**The JPEGs are real.** `file` confirms e.g.
`00039_Game__CAStage.jpg` = `JPEG image data, JFIF standard 1.02, Exif ... Adobe
Photoshop CS Windows, ... 800x600`, 133,672 bytes, `FFD8`…`FFD9`. This is the
same file the earlier log noted at offset 1041409. The README's caveat was right
that the *volume* was wrong (15 counted vs 4,781 real entries) but the JPEGs
themselves are genuine — they were simply lost among 4,700+ engine tables.

### 6b. The remaining 1,324: keystream-encrypted (named lead, not solved)

The `Map/*` payloads are the clearest case: FxMap has **exactly 893** of them —
*the same number the old tool counted as "893 zlib streams"*, so the old scan was
finding these files and failing to open them, not finding real streams.

They are **not** stored, and **not** compressed. They are encrypted with a
**position-based keystream**, and the keystream is partly **exposed**. Viewing a
payload as u32s where the plaintext values are small integers (so their high
three bytes are zero), those high bytes reduce to the keystream itself. Measured
across 200 FxMap `Map/*` payloads:

```
u32[1].bytes[1:4] == 44 71 9c    on 200/200     (low byte varies: 9 values)
u32[2].bytes[1:4] == e3 1b 9c    on 200/200     (low byte varies: 6 values)
u32[3].bytes[1:4] == a1 61 9d    on 200/200     (low byte varies: 14 values)
u32[0]                           varies fully
```

So the keystream at offsets 5–7 is `44 71 9c`, at 9–11 `e3 1b 9c`, at 13–15
`a1 61 9d` — **three direct keystream samples**. The period is not 4 (those three
disagree), so it is a longer generator: recover `k(i)` from the constant-byte
runs, then apply it. This is precisely the "position-based stream" NOTES.md §2
left open and matches the Zenhax note ("something like 256 different
operations"). **Ruled out** for these: raw deflate at any offset; stored flat
(zlib-inflate of the whole payload); the self-differential `.idx` cipher; and
fixed-XOR (only *some* bytes are constant, not all).

Ruled out as a whole-payload key too: within-archive payload pairs of similar
size XOR to 5.95–7.95 bits/byte, so no cheap fixed keystream shared per archive.

**Important scope note:** most of these encrypted payloads are `Map/*` map data,
`MapScriptTemplate/*`, and object/attr tables. They are **not** where the image
and audio assets live — those are in the 40,349 `table` records, the 907 zlib
records, and the 838 validated jpg/ogg files, all of which are extracted.

## 7. Files

| file | role |
|---|---|
| `scripts/idx_idd.py` | **the format core** — `read_index()`, `carve()`; documented and importable |
| `scripts/idx_walk_big.py` | CLI walker; writes `work/idx_layout/walk_big.json` (43,425 names) |
| `scripts/idd_carve.py` | carve + per-payload header validation, per-archive coverage |
| `scripts/extract_assets.py` | the extractor; now drives the exact idx carve first (`--magic-only` restores the old path) |

Run:
```bash
python3 -I scripts/extract_assets.py --dry-run    # 43,425 entries, 1086.2 MB, 100.00%
python3 -I scripts/extract_assets.py              # writes work/assets/by_index/<archive>/
python3 -I scripts/idx_walk_big.py                # just the index walk
```

## 8. Rules that survived

Nothing here contradicts the repo's verification standard; it reinforces it:

- **Sizes come from the index, then are validated by parsing each payload's own
  header.** A magic hit is still not an asset count.
- The `sum(sizes) == file size` identity is the coverage check, and it is exact.
- Actual record counts come from walking, **never** from the header's claimed
  count.

## 9. Ruled out along the way (named dead ends)

- **Per-record XOR chains** (NOTES.md §8's model) — wrong; the chain is global.
- **Directory-prefix guessing** for the seed — unnecessary; the seed solves.
- **Extension filters** on names — fatal; names have no extensions.
- **Assuming `[u32 len][name]`** prefix framing — wrong; length lives in the
  *previous* record's trailer.
- **Magic-carving images out of the big archives** — the payloads are engine
  tables, not files; carving found <1% and the rest is not image data at all.
- **The `.idd`'s own leading rectangle/table** — it is a payload of payloads, not
  a global header.
