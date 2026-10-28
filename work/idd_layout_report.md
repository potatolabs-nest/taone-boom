# .idd layout investigation — working log

## Confirmed so far (validated against bytes)

### 1. zlib record layout: `[u32 comp_size][u32 infl_size][zlib stream]`
- FxMap.idd: 893/893 zlib streams have `u32@(i-8)==compressed_bytes` AND
  `u32@(i-4)==inflated_bytes`. **893/893 exact, zero mismatches.**
- FxDesktop.idd: 14/14 exact.
- These records are **fully contiguous**: FxMap's 893 records run
  0xe5575 → 0x6ef5bc with zero gaps (6,332,487 bytes = 7.02% of file).
  Every record header starts at the exact byte after the previous stream ends.
- Run in FxDesktop is broken into segments (4 gaps).

### 2. Coverage implications
- FxMap.idd 90,223,416 B: zlib records = 6.33 MB (7.02%).
  head before run = 939,381 B (1.04%). tail after = 82.95 MB (91.9%),
  entropy ~7.99 (random-like → compressed or encrypted, NOT zlib).

### 3. Real embedded JPEGs in "hard" archives (strict segment-chain validated)
- FxStage 42, FxContents 45, FxDesktop 68, FxMap 43, FxMonster 3.
- FxStage @1041409 is a genuine JFIF/Exif Photoshop JPEG, extent 133,672 B.
- FxCharacter.idd: ZERO strict JPEG, zero DDS, zero BMP. (hardest)

### 4. The descriptor table does NOT store payload offsets
- No 4-byte-aligned value anywhere in FxMap's first 940 KB equals any zlib
  stream offset. So the head table is not an offset index.
