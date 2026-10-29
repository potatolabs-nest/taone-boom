# Large Fx*.idx name decoding — status

## SOLVED: the transform

Both index families use one transform, verified against real records:

    name[i] = stem[i] ^ name[i-4]   for i >= 4
    name[i] = stem[i] ^ k           for i == 0
    name[i] = stem[i]               for 1 <= i <= 3      (PLAINTEXT)

Only one byte, `k`, is unknown per archive.

## Verified decodes (ground truth)

| archive        | k      | decoded name                     |
|----------------|--------|----------------------------------|
| `FxStage.idx`  | `0x17` | `Game/AIBattle_SuperStar`        |
| `FxMonster.idx`| `0x18` | `Monster/AquaMon00_Appear`       |
| `FxSound.idx`  | `0x0a` | `MP3/Aliens`                     |

Each was confirmed against the record's own following bytes, not by
self-consistency: FxStage record 0 is followed by `u16 4` and the literal
short name `Star`, matching `Game/AIBattle_SuperStar` exactly.

## Why `stem[1:4]` being plaintext matters

It is readable without any decryption and names the directory immediately:

| archive     | `stem[0:4]`    | reads as | directory    |
|-------------|----------------|----------|--------------|
| `FxSound`   | `47 50 33 2f`  | `?P3/`   | `MP3/`       |
| `FxMonster` | `55 6f 6e 73`  | `?ons/`  | `Monster/`   |
| `FxStage`   | `50 61 6d 65`  | `?ame/`  | `Game/`      |

## Remaining problem: per-archive `k` and framing

`k` cannot be read off directly. Two attempts to recover it automatically both
failed, and both are recorded here so they are not retried:

1. **Requiring the whole stem to be printable** — produced zero results. The
   stem is longer than the name: the name is followed by NUL padding and binary
   fields, so the decode must be truncated at the first non-path byte.
2. **Scoring `k` by how often a directory repeats** — unreliable. On FxMonster it
   happens to give the right `k` (`0x18`), on FxStage it gives `0x00` when the
   true value is `0x17`. The scoring surface is too flat to be trusted.

What does work is the naive 256-way search with **truncate-then-validate**:
decode, cut at the first byte outside `[A-Za-z0-9_/.-]`, then require a `/` and a
contained extension. That is how all three verified names above were obtained.
`scripts/idx_big.py` implements it; it is correct but does not yet pin `k`
automatically across every archive.

## Next step for whoever picks this up

The record framing is still not pinned for the big family, and that is the real
blocker, not `k`. Record 0 of FxStage has no length prefix — the stem begins at
byte 16 — while later records appear to carry one. Once the stride is known, `k`
falls out trivially, because a correct `k` makes every record decode and a wrong
one desynchronises the walk.
