#!/usr/bin/env bash
# Copy the REAL extracted manifest + asset tree into app/public/ so the static
# app serves them from one directory.
#
# The manifest's `file` values are relative to the manifest's own directory
# (work/assets/), so the whole tree is mirrored into app/public/ unchanged.
#
# Usage:  app/sync.sh
# Idempotent: safe to re-run after every extractor run.

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$APP_DIR/.." && pwd)"
SRC_MANIFEST="$REPO_DIR/work/assets/manifest.json"
SRC_ASSETS="$REPO_DIR/work/assets"
SRC_SSI="$REPO_DIR/work/ssi"
DEST="$APP_DIR/public"

say() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

[ -d "$DEST" ] || die "$DEST does not exist"

if [ ! -f "$SRC_MANIFEST" ]; then
  die "real manifest not found at:
    $SRC_MANIFEST

The extractor has not produced one yet. The app already ships a synthetic
fixture at app/public/manifest.json (regenerate it with:
    python3 -I scripts/make_fixture.py
), so you can develop and browse the UI at any time."
fi

say "source manifest : $SRC_MANIFEST"
say "destination     : $DEST"

# --- 1. assets + manifest ------------------------------------------------
# Sync each top-level directory of the asset tree into its own subtree. The
# --delete is scoped to that subtree, never to the app root, so the app's own
# files (index.html, ssidata/, and anything else here) can never be removed.
if command -v rsync >/dev/null 2>&1; then
  say "syncing asset tree with rsync…"
  found=0
  for entry in "$SRC_ASSETS"/*/; do
    [ -d "$entry" ] || continue
    name="$(basename "$entry")"
    say "  $name/"
    rsync -a --delete "$entry" "$DEST/$name/"
    found=1
  done
  [ "$found" = 1 ] || say "  (no asset subdirectories found)"
else
  say "rsync not found — using cp (stale files will not be removed)…"
  cp -Rf "$SRC_ASSETS/." "$DEST/"
fi
cp -f "$SRC_MANIFEST" "$DEST/manifest.json"
say "manifest copied."

# --- 2. decoded ssi strings ---------------------------------------------
if [ -d "$SRC_SSI" ]; then
  say "syncing decoded ssi strings…"
  mkdir -p "$DEST/ssidata"
  # .strings.txt = ASCII string dumps; .bin = original CP949 blobs the app
  # decodes in the browser with TextDecoder('euc-kr').
  find "$SRC_SSI" -maxdepth 1 -type f \( -name '*.strings.txt' -o -name '*.bin' \) \
       -exec cp -f {} "$DEST/ssidata/" \;

  # index.json drives the #/data file picker; regenerate it from what we copied.
  python3 - "$DEST/ssidata" <<'PY'
import json, os, sys
d = sys.argv[1]
files = []
for fn in sorted(os.listdir(d)):
    if fn == "index.json":
        continue
    files.append({
        "name": fn,
        "bytes": os.path.getsize(os.path.join(d, fn)),
        "encoding": "euc-kr" if fn.endswith(".bin") else "utf-8",
    })
with open(os.path.join(d, "index.json"), "w") as f:
    json.dump({"files": files}, f, indent=1)
print("  ssidata/index.json: %d files" % len(files))
PY
else
  say "note: $SRC_SSI not found — #/data will have no source data."
fi

# --- 3. summary ----------------------------------------------------------
python3 - "$DEST/manifest.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
s = m.get("summary", {})
print("manifest ready: %s assets, %s ui_sprites, %s ndadata pak%s"
      % (s.get("total_assets", "?"), s.get("ui_sprites", "?"), s.get("ndadata_pak", "?"),
         "  (FIXTURE)" if m.get("fixture") else ""))
PY

say ""
say "Done. Serve it with:"
say "    cd $DEST && python3 -m http.server 8000"
say "Then open http://localhost:8000/"
