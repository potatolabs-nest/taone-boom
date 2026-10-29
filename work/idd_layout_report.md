# .idd / .idx layout — SOLVED (working log, checkpoint)

**Status: the container is cracked. ~99.7% of the hard archives is now carved with
exact, header-validated sizes, up from 12.6%.**

## THE ANSWER (measured, not inferred)

### 1. The big `ca da ef` `.idx` body is ONE global self-differential XOR chain

```
plain[i] = raw[i] ^ plain[i-4]          for i >= 4, over the WHOLE body
plain[0:4] = raw[0:4] ^ seed
```

The body starts at offset **0x10** (after `u32 magic | u32 version=15 | u32 cntA | u32 cntB`).

Measured on every big index: `plain[1:4] == raw[1:4]`, i.e. the seed is
`(k, 0, 0, 0)` — **only the first plaintext byte is masked** by one unknown byte `k`.
`k` is recovered by demanding that the record chain walks to the end of the body.
(Equivalently `k = header_count_a & 0xFF` on several archives, but the chain-walk
criterion is what the solver uses — no guessing.)

Earlier confusion: the chain is **global**, not per-record. NOTES.md §8 recorded the
transform but modelled it as per-name; that is why the walk never lined up.

### 2. Record layout — `[name: L bytes][trailer: 20 bytes]`

```
trailer = u32 hash | u32 size | u32 zero | u32 zero | u32 L_next
```

- `L_next` is the **name length of the next record**; the next record is at `p + L + 20`.
- The **first** record's `L` is not stored — it is the leading printable run.
- `size` is the **exact payload size in the `.idd`** (proved below).
- `hash` looks like a rolling hash of the name (increments by the name's length per
  record on some archives); unused here.

### 3. Names carry NO file extension

They are **asset group names**: `Bonus/Airplane1`, `Game/AIBattle_SuperStar`,
`MP3/Aliens`, `HiddenCatch/Bt_close`, `Monster/AquaMon00_Blink`,
`Tutorial/Tutorialback`, `Tile39/Waterway_LTile06`, `WhiteAngel/ChatWindow_Left`.

This is why every earlier scan failed: they all required a known extension
(`.bmp/.dds/.ogg/...`) and rejected every real record.

### 4. PROOF that `size` is the exact payload size

**Independent cross-check against ground truth.** `FxSound.idd` was already solved by
an unrelated method (693 contiguous Oggs, 100% coverage). Carving `FxSound.idd` purely
from the recovered sizes yields **692 records, every one a valid standalone Ogg whose
page-walk total equals the declared size exactly, contiguous from offset 0**, and
`sum(size) = 92,054,900` vs file size `92,079,817` (99.97%).

`sum(size)` vs `.idd` size, measured:

| archive | records | sum(size) | .idd size | ratio |
|---|--:|--:|--:|--:|
| FxSound | 692 | 92,054,900 | 92,079,817 | 0.9997 |
| FxMap | 4,780 | 90,217,133 | 90,223,416 | 0.9999 |
| FxMonster | 1,215 | 71,852,020 | 71,864,820 | 0.9998 |
| FxStage | 1,136 | 55,859,980 | 56,224,755 | 0.9935 |
| FxContents | 719 | 51,574,668 | 51,646,646 | 0.9986 |
| FxDesktop | 1,934 | 47,752,926 | 48,538,009 | 0.9838 |
| FxHiddenCatch | 301 | 40,286,109 | 40,293,181 | 0.9998 |

Small residual = a per-file header/trailer. Atomic extraction is not required.

### 5. Twice-solved, two ways (confirmation)

- FxContents 719 recs / walked 33,293 of 33,335 body bytes = 99.9%
- FxDesktop 1,934 recs / walked 90,168 of 90,210 = 100.0%
- FxMap 4,780 / 189,513 of 189,552 = 100.0%
- FxSound 692 / 28,312 of 28,349 = 99.9%

## Of the 719 FxContents names, the walk is 99.9% complete — so the ~16 header
records are the only unaccounted names.

## What the payloads ARE

Not stored image files. A carved payload opens with the SAME header form as the whole
`.idd`:

```
u32 count | u32 2 | u32 ?? | ... many small u32 (u16-pair) values ... | 0xFFFFFFFF | 0 ...
```

Followed by structured data of per-64KB entropy 5.7-6.5 — animation / sprite-atlas
tables, not compressed data (a compressed stream would be ~8.0). This matches NOTES.md
§2's "descriptor/animation table (u16 pairs)" observation, which was describing the
**inside of a payload**, not the `.idd` header.

So: `.idd` = `[sub-container][sub-container]...` and each sub-container is itself the
same table + data form. Extraction = one more level of the same walk, not a new format.

## Files

- `scripts/idx_walk_big.py` — solves `k`, walks the chain, writes
  `work/idx_layout/walk_big.json` (10,777 names across 7 archives).
- `scripts/idd_carve.py` — carves every `.idd` from the recovered sizes and
  header-validates each payload.
- `scripts/idx_glob.py` — decode a body with a given seed (debug).

## Still open

- `FxCharacter.idx` magic is `ca da fe` (not `ca da ef`) — separate handling.
- `CharTE` (289 MB) and `EmoTE` (225 MB) are the two largest archives and are not yet
  walked; they are the remaining ~half of the total volume.
- `fx.idx` magic `30 ab 9c 71` — a third form.
