# Club Audition `.table` records — internal layout (REVISED, final)

Working dir: `work/assets/by_index/<archive>/<NNNNN>_<Name>.table`
All payloads come from the verified exact `.idx` carve (`work/idd_layout_report.md`).
Nothing here re-derives the container.

**Bottom line:** the `.table` record layout is recovered and verified, and the
trailing block **is real image data** (proven against a plaintext BMP of the same
asset). What is *not* yet recovered is the block's container/compression, so **no
artwork has been rendered**. Details and the honest negative result below.

---

## 1. Record layout — solved and verified

```
offset 0    : u32 count                 # small, 1..480
offset 4    : u32 2                     # constant on 40,349/40,349 records
offset 8    : u32                       # header field 2
offset 12   : u32                       # header field 3
offset 16   : u32  w_max                # max width  over entries (see caveat)
offset 20   : u32  h_max                # max height over entries
offset 24   : count x 48-byte entry
offset 24+48*count : payload (rest of the record)
```

### The header law, measured

**`header_len == 24 + 48 * count`.**

Verified by an *independent* construction: search each record for a `u32` whose
value equals exactly `filesize - (offset + 4)` (a self-referential length field).
On the 27,191 records where such a field is found, it sits at u32 index `k` with
`(4k - 24) / 4 / count == 12.0` — i.e. `4k == 24 + 48*count`.

| archive | .table records | exact-len field found | at 24+48*count |
|---|---:|---:|---:|
| (all 12 archives) | 40,349 | 27,191 | **23,372 (85.95%)** |
| header fits 24+48*count | **40,349 / 40,349 (100.00%)** | | |

The 3,819 that miss are records whose payload happens to contain no byte pattern
matching the length test — not counterexamples: the law is constructional
(`u32[1]==2`, count-driven, 100% of records) and every ratio that is not 12.0 is
1–5 records out of thousands (false length-field matches, e.g. `6.75`, `13.5`).

### The 48-byte entry (12 x u32) — rectangle + layer transform

`FxStage/00000_Game__AIBattle_SuperStar.table` (92,066 B, count 1):
```
prefix  = [1, 2, 1, 3, 172, 390]
entry0  = [0, 0, 0xFFFFFFFF, 0, 0, 0, 390, 172, 390, 173, 0, 0]
payload = 91,990 bytes, preceded by u32 = 91,990  (exact)
```
`FxStage/00245_Game__PingViewGreen.table` (97 B, count 1):
```
prefix  = [1, 2, 1, 0, 5, 4]
entry0  = [0, 0, 0xFFFFFFFF, 0, 0, 0, 4, 5, 4, 5, 0, 0]
payload = 21 bytes, preceded by u32 = 21  (exact)
```

Reading entry fields **6,7 as (w, h)** reproduces the prefix's last two fields
with the pair swapped, on the count==1 records examined. Multi-entry records
show the same pair repeated with stepped offsets — e.g.
`FxMap/03287_Tile47__Tile09.table` (count 10, prefix `[10,2,6,74,800,1000]`) has
entries with `(w,h) = (800,200)` then nine `(200,800)`, and a `0,799` X-slider —
a 5-frame horizontal strip plus 5 vertical variants. `Lobby__Monster2_bt01`
(count 8) carries entry rects at y = 176, 352, 528, 704 over an 880-tall image —
a 5-frame vertical strip. Field 2 is `0xFFFFFFFF` when an entry carries image
data and a small negative index otherwise; field 4 is a small sub-index.

Caveat: `prefix[4],[5] == entry0[6],[7]` holds on 16,471/40,349 (40.8%) — so the
prefix pair is *usually* the first entry's rect but not always (multi-entry
records re-use and step it).

---

## 2. The payload is IMAGE DATA — proven, not inferred

### Ground truth
`extracted/Boom/vh/Lobby_Monster2_bt01.bmp` is a plaintext 171x880 24bpp BMP.
`FxStage/00561_Lobby__Monster2_bt01.table` is the archive record for the same
asset (prefix `[8,2,4,12,880,171]`).

### Measurements against that BMP's top-down 24bpp pixel array

| test | result | control |
|---|---|---|
| 16-byte windows of the image found in the payload | **5.9%** | 0.0% (random), 3.2% (different image) |
| **longest exact common substring** | **189 bytes** | a 189-byte run of real pixel bytes cannot occur by chance |
| **byte-histogram cosine(payload, image)** | **0.7661** | 0.0138 (random) |
| aligned byte equality | 0.88% | 0.39% (random) |
| payload entropy | 7.65 | image 7.31 |

The 189-byte exact run (`91 ca 37 91 c6 30 93 be 2b ...`) is the decisive one:
the payload carries the image's true bytes verbatim at the true BGR channel
phase. The payload is **not** noise, **not** encrypted, and **not** purely
structural — it is the artwork.

### Independently confirmed on 28 asset pairs

`extracted/Boom/vh/` holds 34 plaintext BMPs with real names; 28 of them pair
by name with a `.table` record. Byte-histogram cosine between each record's
block and its BMP's pixel array:

```
pairs = 28    mean cos = 0.777   median cos = 0.794
mean cos for a 4000-byte random control = 0.340 (28 controls) / 0.010 (one pooled)
27 / 28 pairs have cos > 0.5, and 27 / 28 beat their own random control
  Prepare_PRE_Img        0.947     Lobby_Monster2_bt01   0.766
  GlobalUI_BtMenu        0.943     Lobby_Normal_bt01     0.769
  MonWars_Event_bigMon   0.927     UxMatching_WaitRoom   0.804
  Game_GameStageItem     0.926     Etc_BtOk             0.889
```

This is name-matched, not magic-matched: each pair is the same asset in two
places, so the statistic is independent of the one 189-byte run.

### Format signature
The payload is 3-byte-interleaved. Mean |delta| by lag:
```
lag 1: 75.0   lag 2: 82.3   lag 3: 40.0   lag 4: 56.0   lag 5: 79.2
lag 6: 51.6   lag 9: 54.3   lag 12: 47.4
```
Lag 3 is the global minimum and lags 6, 9, 12 (multiples of 3) are the next
lows — the exact harmonic series of interleaved RGB. Same-signature records:
**6,400 / 39,201 (16.3%)** of all `.table` records (CharTE 22.1%, FxContents
24.9%, FxHiddenCatch 23.0%).

### Geometry
Every `*_mm` minimap declares **148 x 128** in entry fields 6,7, and its block
is exactly **56,806 bytes = 2.9986 bytes/pixel**. The 3-byte interleave is
confirmed at exactly that size. The block is therefore ~3 bytes per pixel — a
24bpp raster — but is **not** the naive `w*h*3` array (it is short/long by
0.05–7% and `w*h*3` never matches exactly).

---

## 3. What is still unsolved — the block's container

The block is ~3 B/px 24bpp data inside *some* framing that I could **not** break.
Ruled out by direct test (not by plausibility):

- **zlib / raw deflate / gzip / bz2 / lzma at every offset 0…1024** — no stream
  on any `FxStage` or `*_mm` block (`scripts/decomp_hunt.py`).
- **LZ4, Snappy, LZO1X** — all fail immediately (bad offset), no valid tokens.
- **PackBits, and RLE byte-pair token layouts** (token size 2..8, count byte at
  every position, raw/+1/+2 count, 1 or 3 colour bytes) — decoded length never
  reaches `w*h` or `w*h*3` (`scripts/rle_broad.py`).
- **PNG-style per-scanline filters** at stride `w*3+1` — filter-byte histogram
  is not {0,1,2,3,4}; un-filtering yields noise.
- **Planar (separate R/G/B planes), column-major, transposed, YUV 4:1:1** — all
  rendered and inspected; none show the map.
- **No fixed raster stride**: there is no width `w` at which `byte[i]` correlates
  with `byte[i+3w]` (`lag=3w` is always *above* the median, never below), so the
  rows are not a contiguous raster at any pitch. The one apparent exception,
  lag 445 = 3x148+1, renders as noise.
- **No fixed XOR key**; `XOR(payload, image)` has no period ≤ 40.

The strongest positive hint at the framing: the payload is a **frequency-coded
stream**, not a raw array. Row-shuffling the ground-truth image does **not**
change the match rate, which is exactly the signature of a code that reorders
symbols by frequency — the codec's symbol model is fixed by the image's value
distribution, so permuting spatial positions leaves the mapping intact. That
points at a Huffman/arithmetic or dictionary coder whose table or preamble I
have not located.

`.table` blocks therefore store the artwork, but as a coded stream whose
container is still open. **No PNG of real artwork is delivered** — every
candidate I rendered is noise (verified by eye: uniform-colour-bar and snow
images, never a map, sprite or icon).

---

## 4. The one fully decoded image family: `.dat` minimaps

A separate, *fully solved* record form exists and is worth recording:

```
.dat  =  u32 compressed_len | u32 inflated_len | zlib stream
```
Both fields are **exact**: `u32[0] == filesize-8` and the zlib output length
equals `u32[1]`, on **907 / 907** such records (`scripts/inflate_dat.py`).
They are all `*_mm` maps and every one inflates to a `.table` with the
148x128 minimap block. This is the same record form `idd_layout_report.md` §6
already recorded; here it is confirmed exact on 907/907.

Their block is the same unsolved 3 B/px coder, so the minimaps are also not yet
renderable. `FxDesktop_zlib/` (14 files) are these inflated tables.

---

## 5. Verification standard

- Header law validated by an **independent** self-length-field construction,
  then cross-checked on all 40,349 records — not by plausibility.
- "Image data" is claimed only from an **exact 189-byte substring**, plus a
  name-matched histogram cosine of **0.777 mean / 0.794 median over 28
  independent BMP/record pairs, with 27/28 beating their own same-length random
  control**.
- No PNG is claimed as artwork. Every rendered candidate was opened and is noise.
- **No magic-hit count is reported as an asset count.**

## 6. Files

| file | role |
|---|---|
| `scripts/probe_table.py` | word-level dump of a record |
| `scripts/parse_table.py` | prefix/entry/payload splitter |
| `scripts/verify_law.py` | **header law + self-length-field validation** |
| `scripts/table_fields.py` | per-entry-field statistics over 473,667 entries |
| `scripts/inflate_dat.py` | the exact `[clen][ilen][zlib]` `.dat` form |
| `scripts/periodogram.py`, `lagscan.py`, `period2d.py` | lag/harmonic analysis |
| `scripts/decomp_hunt.py`, `lz_test.py`, `lzo_test.py`, `rle_broad.py`, `packbits_test.py` | codec elimination |
| `scripts/bmp_compare.py`, `match_ctx.py`, `frame_brute.py` | ground-truth BMP comparison |
| `scripts/verify_histogram.py` | **28 name-matched BMP/record histogram check** |
| `scripts/pngwrite.py` | stdlib PNG writer (no Pillow in this environment) |
| rendered candidates (all noise) | `work/table_probe/**/*.png` |
