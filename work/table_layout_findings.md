# Club Audition `.table` record layout — partial findings (in progress)

Working dir: `work/assets/by_index/<archive>/<NNNNN>_<Name>.table`
All payloads here came from the verified exact `.idx` carve (see
`work/idd_layout_report.md`). Nothing below re-derives the container.

## Established so far (measured, not guessed)

### 1. A `.table` is `[prefix: 24][count x 48-byte entry][payload]`

```
u32 count            # u32[0], small (1..480)
u32 2                # u32[1] == 2 on 40,349/40,349 records (known)
u32 A, B, C, D       # 16 more bytes of prefix
count x 48-byte entry
payload (rest of the record)
```

**Header law (new, measured): `header_len == 24 + 48 * count`.**

Verified by finding, in each record, a `u32` field whose value equals exactly
`filesize - (offset + 4)`. Where such a field exists its u32 index `k` satisfies
`4*k == 24 + 48*count` with ratio histogram `(hdr-24)/4/count == 12.0`:

| archive | tables | records with exact len field | ratio 12.0 |
|---|---:|---:|---:|
| FxStage | 1,122 | 798 | 438 |
| CharTE | 17,557 | 8,902 | 4,777 |
| FxMap | 2,571 | 2,015 | 1,710 |
| fx | 3,386 | — | 1,204 |
| EmoTE | 8,509 | — | 4,110 |
| FxCharacter | 3,116 | 227 | 101 |
| FxDesktop | 1,887 | — | 1,240 |
| FxContents | 698 | — | 306 |
| FxMonster | 1,214 | — | 179 |
| FxHiddenCatch | 279 | — | 48 |

Every other observed ratio (`6.75`, `13.5`, `8.25`) is 1–5 records out of
thousands and is a *false* length-field match, not a counterexample.

### 2. The 48-byte entry looks like a sprite/atlas rectangle + layer transform

Example — `FxStage/00000_Game__AIBattle_SuperStar.table` (92,066 B, count 1):
```
prefix  u32[0:6] = [1, 2, 1, 3, 172, 390]
entry0  u32[0:12] = [0, 0, -1, 0, 0, 0, 390, 172, 390, 173, 0, 0]
payload            = 91,990 bytes, preceded by u32 = 91,990 (exact)
```
`FxStage/00245_Game__PingViewGreen.table` (97 B, count 1):
```
prefix  = [1, 2, 1, 0, 5, 4]
entry0  = [0, 0, -1, 0, 0, 0, 4, 5, 4, 5, 0, 0]
payload = 21 bytes, preceded by u32 = 21 (exact)
```
`FxStage/00061_Game__ColoringBar_Blue.table` (153 B, count 1):
```
prefix  = [1, 2, 1, 0, 19, 1]
entry0  = [0, 0, -1, 0, 0, 0, 1, 19, 1, 19, 0, 0]
payload = 77 bytes, preceded by u32 = 77 (exact)
```

Reading entry fields 6,7 as `(w, h)` reproduces the prefix's last two fields with
the pair swapped, on every count==1 record examined:
`SuperStar (390,172)`, `PingViewGreen (4,5)`, `ColoringBar (1,19)`.

### 3. Payload is NOT a plain w*h pixel block

Tested `payload_len == sum(w*h) * bpp` for bpp in {1,2,3,4} over FxStage,
CharTE, FxCharacter, FxMap: **no consistent match** (FxStage 0/1122 exact).
So the payload is not a naive uncompressed image of the rect.

### 4. But the payload bytes are colour-shaped, not noise

`ColoringBar_Blue` payload vs `ColoringBar_Red` payload — same size (77 B),
same 4-byte framing, different colour channels:
```
Blue:  c0 01 ff ec | 80 01 ff ea | 80 01 fe e8 | 80 01 fc cd | 00 01 fb c9 ...
Red :  c0 01 a1 a1 | ff 01 a0 9f | fe 01 9e 9e | fc 01 39 38 | f5 01 34 34 ...
Blue2: c0 01 ff fc | 80 01 ff fa | 80 01 ff f8 | 80 01 ff eb | 00 01 ff e7 ...
Red2 : c0 01 a7 a7 | ff 01 a6 a6 | ff 01 a4 a4 | ff 01 45 43 | ff 01 3f 3f ...
```
Every other byte is identical across the pair and only the colour channel
changes — the payload is a colour ramp / gradient, 24-bit-ish, framed in
4-bit groups whose high nibble (0xc0, 0x80, 0x00) shrinks monotonically.

`AIBattle_SuperStar` payload shows the same shape at scale: recurring
`01 e5 e6 e7` (near-transparent off-white), `bf bf bf bf`, `93 bf b3`,
`42/43/44/45/47/49 ff ff ff` (near-white, varying low byte) — i.e. an
**ARGB-ish byte stream of one pale colour**, alpha-modulated.

### 5. Header u32[2] == 0xFFFFFFFF is a "no image" sentinel

`entry[2]` is `-1` on records with a payload, and `0xFFFFFFFE`/`0xFFFFFFF2`/… on
some entries of multi-entry records — a negative index, not a colour.

## Open

* The payload framing (the `c0 01` / `01 e5 e6 e7` markers) is not yet decoded.
* Whether any record holds *pixel data* at all, vs purely UV/timing tables,
  is not yet established. See `work/table_layout_findings.md` (this file) — it
  will be updated rather than replaced.
