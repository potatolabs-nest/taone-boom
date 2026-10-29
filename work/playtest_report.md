# Play-test report — Crazy Arcade maze game

Target: `/Users/hieu/Workspaces/taone/deploy/index.html` (source `/Users/hieu/Workspaces/taone/app/public/arcade.html` — the two files are byte-identical).
Method: headless Chrome driven over the DevTools Protocol (`Input.dispatchKeyEvent`, `Input.dispatchTouchEvent`), instrumenting the live `G` object frame by frame. Scripts in `/tmp` (`drive.js`, `timeseries.js`, `final_probe.js`, `probe2.js`, `mobile.js`, `bombblock2.js`, `filetest.js`).

## Warning: the file changed twice while I was testing

`index.html` was rewritten twice underneath this session by another process:

- Start of session: `391` lines, `MAZE` beginning `~#.#.#.#.#.#~`.
- 23:07: `421` lines, with a temporary `__dbg()` overlay and `window.__keytest()` hook injected.
- 23:08 — commit `f7f0cae` "Make the maze actually playable - the old map was a wall grid": 390 lines, `MAZE` replaced with the generated layout, debug hooks removed.

Everything below is against the file as of `f7f0cae` + my one-line fix. I re-verified `md5` stability (three reads over 6 s, unchanged) before finalising.

## Verdict: the game IS playable now

At the current revision the game starts, renders, and responds to keyboard, WASD, the on-screen d-pad (mouse and touch), on desktop and mobile viewports. The two defects that made it unplayable have both been dealt with — one by `f7f0cae`, one by me.

## Defects, ranked

### 1. CRITICAL — the start tile was a hard wall; the maze was a dead 3-tile pocket (fixed by `f7f0cae`)

**Observed.** On the pre-`f7f0cae` revision (reconstructed to `/tmp/playtest_orig/`, served on :8972), driving real arrow keys gave:

```
up    -> 1,1   (no move)
down  -> 1,2
left  -> 1,1   (no move)
right -> 2,1
```

Reachable floor from the spawn: **3 tiles**. Holding ArrowRight for 500 ms advanced the player exactly one tile.

**Cause.** `MAZE` row 1 was `"~#.#.#.#.#.#~"`, so `MAZE[1][1]` is `'#'` — the player spawns on a hard wall. Worse, `G.grid` is never mutated at reset (only `explode()` writes to it), so that `'#'` can never be removed. BFS over the original map: 62 open tiles total, only **3 reachable from the start**, 59 unreachable. The rest of the maze was also a lattice of isolated single tiles — from any tile, the checkerboard wall pattern left at most 2 legal moves, and the reachable region could never grow.

This is what "can't play" looked like: movement was working correctly, there was simply nowhere to go. `f7f0cae` replaced `MAZE` with a layout whose start tile is `.` and which flood-fills to all 79 open tiles (longest shortest-path 18 steps).

**Verified.** The committed replacement is genuinely connected — independent BFS in `/tmp/maze_bfs.py` confirms 79/79 reachable, and a winnability check (`/tmp/winnable.py`) confirms all 36 bricks are destroyable at `power=1` and the post-clear interior is fully connected, so `CLEAR!` is achievable.

### 2. HIGH — an exploded bomb permanently blocks its tile (FIXED, verified)

**Observed.** `passable()` re-checked the exploded tile and returned `false`, so the player could never re-enter a tile where a bomb had gone off. Clean isolation (`/tmp/bombblock2.js`, corridor on row 5, player at x=3 → x=5 → walks left):

```
step5_bombDone:  true          // the bomb HAD exploded
step6_flamesGone: true         // and the flames were long gone
step9_passable_3_5_AFTER_EXPLOSION: false     // yet the tile stayed solid
step11_playerEndedAt: "4,5"    // stopped dead at x=4
step12_STUCK_AT: "yes - stopped at x=4, cannot enter x=3"
step14_permanentlyImpassable: true
```

**Cause.** `deploy/index.html:127` (and the same line in `arcade.html`):

```js
for (var i=0;i<G.bombs.length;i++) if (G.bombs[i].x===x && G.bombs[i].y===y) return false;
```

`dropBomb()` and `tick()` both guard reaped bombs with `!b.done`, but `passable()` does not — it blocks on *any* entry in `G.bombs`, live or spent. And `tick()`'s "reaper" never actually reaps: `G.bombs = G.bombs.filter(function(b){ return !b.done || b.t < 999; })` — for an exploded bomb `b.t` keeps incrementing from 0 and only passes 999 after **999 s**, and `b.t` also stops advancing once the game is over. So exploded bombs queue up in `G.bombs` for the whole session.

**Why this is the real "can't play" blocker** rather than a cosmetic one: the UI says "Space drop bomb" and tapping the canvas drops a bomb, so the first bomb a player drops walls off the tile they were standing on — and the bomb sits directly on their only route through a 1-wide corridor (as in the BFS above, the maze is largely corridors). Repeat it a few times and the level grids itself shut, with no feedback and no way to recover except `R`. This is precisely the "I can't play" report.

**Fix applied** (`deploy/index.html:127` and `app/public/arcade.html:127`, one line each):

```js
for (var i=0;i<G.bombs.length;i++) if (!G.bombs[i].done && G.bombs[i].x===x && G.bombs[i].y===y) return false;
```

**Verified after the fix.** `step9_passable_3_5_AFTER_EXPLOSION: true`, `step11_playerEndedAt: "1,5"` (walks straight back through), `step14_permanentlyImpassable: false`. Live bombs still block correctly (`step3_passable_3_5_whileLive: false`) — dropping a bomb on yourself still stops you re-entering it while it is live, which is the intended behaviour. Logic self-test still passes end to end.

### 3. MEDIUM — every tile takes exactly one 60 Hz frame at any speed; movement ignores `dt`

**Observed.** `dt` samples passed into `step()` are a flat `~0.0167` (60 fps). Player and enemies both cross a 10-tile corridor in **164–165 ms ≈ 61 tiles/s**. The intent in the code is `sp = 4.2` tiles/second, which `step()` uses *only* as the easing constant `k = dt*sp` for the sprite, never to gate the logical step.

**Cause.** `deploy/index.html:132-142` — `step()` moves a whole tile (`G.px = nx`) on every call regardless of `dt`, and `tick()` calls it unconditionally at 60 Hz. So the true speed is 1 tile per frame, i.e. 60 tiles/s at 60 Hz, 120 tiles/s on a 120 Hz display. `enemiesStep()` (`:150-157`) has the identical structure.

This is not why the game was unplayable, but it makes it a twitch game rather than the intended 4.2 tiles/s, and it is the reason a real player dies fast in the corridor (the 60 Hz enemy crosses a corridor in ~165 ms — you cannot react). Confirmed lethal rather than incidental: with an enemy adjacent to the player, three lives drain in **181 ms** (~12 frames) — no invulnerability window exists (`G` has no `invuln`/`grace`/`hitT` field, and `hurt()` has no cooldown), so an adjacent enemy drains all lives in consecutive frames.

**Minimal fix** — accumulate elapsed time per tile instead of moving per call, e.g. give each of the player and enemies a `moveAcc` and only step when `moveAcc >= 1/sp` (`sp` = 4.2 for the player, ~2.2 for enemies), zeroing it on each tile move; keep `dt` for the `fx`/`fy` easing. I did **not** apply this: it changes game feel (the tuning question of how fast the game should be is a design call, not a defect with one unambiguous fix), and it is a behavioural change beyond the "small and unambiguous" remit. Flagging it because it dominates the difficulty.

### 4. LOW — the `time` clock runs ~35% slow

`G.time -= dt` (`:296`) is driven by rAF `dt`, measured at 0.0167 while wall time advances ~0.0250 per frame in headless (`performance.now()` moves ~25 ms per 16.7 ms `dt`). Over 8 fresh loads, 8 s of wall time consumed only ~5.9 s of `G.time`. Cosmetic; the same `dt` is used by the easing. Not fixed.

### 5. LOW — `favicon.ico` 404

Logged on every load (`Failed to load resource: 404 /favicon.ico`). Harmless.

## What passed

| Check | Result | Evidence |
|---|---|---|
| Game starts | **PASS** | `ready=6/6`, `running=true`, `G.grid` 11 rows |
| All 6 tiles load over HTTP | **PASS** | six `200`s, `naturalWidth` 64/64/64/64/96/96, no `Network.loadingFailed` |
| JS exception on load | **PASS** | zero `Runtime.exceptionThrown`; no console errors |
| rAF loop runs | **PASS** | 122 frames / 2005 ms = 60.9 fps; `G.time` advances |
| Arrow keys move the player | **PASS** | real `dispatchKeyEvent` hold: `px 1→5`, `keys={right:true}` while held |
| Key detection / `preventDefault` | **PASS** | `MAP[e.key]` matches `ArrowRight`; `preventDefault` blocks scrolling without blocking the handler |
| Sprite easing `G.fx` | **PASS** | logical `px=5` while `fx` leisurely trails at `4.88` |
| Canvas renders | **PASS** | 128700/128700 px painted (390×330); screenshot shows floor, water border, hard walls, soft bricks, Bazzi, skull, HUD, d-pad |
| Canvas sized correctly | **PASS** | backing store 390×330 = 13·30 × 11·30, CSS 720×610, `image-rendering:pixelated` |
| Space drops a bomb | **PASS** | `bombs=1` |
| Touch d-pad | **PASS** | mouse and synthetic `touchStart/touchEnd` both set `keys.right`, move the player, and clear on release |
| Mobile 375×812 | **PASS** | canvas and all four d-pad buttons on-screen and `hittable`; `docScrollable:false` |
| Self-test `?test=1` | **PASS** | `maze=13x11 | move=ok | wall=ok | bomb=ok | flames=ok | brick=ok | enemies=ok | pickup=ok | PASS` |

## Two things worth noting, neither a defect

- **`file://` works too, and does not kill the loop.** I tested the stated failure mode directly. Chrome blocks each `tiles/*.png` (`onerror` fires, `naturalWidth` stays 0), but the images come back `complete:true`, so the `img.complete` guards in `draw()` pass and `drawImage()` silently no-ops on a broken image. `ready` still reaches `6/6`, `running=true`, `G.time` advances, and real arrow keys move the player. The board renders as a flat green plane with the Bazzi sprite and HUD — ugly, but *playable*, not a hard blocker. So a `file://` user would report "the tiles are missing", not "I can't play".
- **"Can't play" really was the maze, not wiring.** I specifically tested the "needs a click first" and "positioned offscreen" hypotheses: `document.hasFocus()` is `true`, `body` is a flex-centred `overflow:hidden` container, canvas at `top:83.9` and the d-pad at `703–816` inside a 900 px viewport with `scrollHeight` 900 — nothing is clipped or offscreen. Filling the genuinely diagnostic test — the four-direction mobility matrix from the spawn — is what produced the 3-tile dead pocket in defect 1.

## Files changed

- `/Users/hieu/Workspaces/taone/deploy/index.html:127` — added `!G.bombs[i].done` to the bomb check in `passable()`.
- `/Users/hieu/Workspaces/taone/app/public/arcade.html:127` — identical change (files remain byte-identical).

Not committed. Defect 3 (per-frame movement) and defect 4 (clock) are reported but deliberately left unfixed.
