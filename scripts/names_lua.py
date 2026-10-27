#!/usr/bin/env python3
"""Recover real asset filenames from the Lua UI scripts in ndadata/*.idd.

Some ndadata bundles are compiled Lua (Lua 5.0 bytecode: header 1b 4c 75 61 50).
Their string constants are stored as [0x04][u32 len][bytes], and those constants
contain real, usable asset paths — Quest/..., PopupEvent/... etc. That is genuine
plaintext naming for the popup/quest UI, which the .idx cipher otherwise hides.

Note the limit: this works only for the Lua-shaped ndadata bundles. The large
archives (FxSound, FxMap, ...) begin with [u32][u32 2] struct records, not Lua,
so their contents are not named this way.

Usage: python3 -I names_lua.py
Writes: work/ndadata_names.json
"""
import collections, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NDADATA = os.path.join(ROOT, "extracted/Boom/ndadata")
OUT = os.path.join(ROOT, "work/ndadata_names.json")

LUA_SIG = b"\x1bLua"
ASSET_RE = re.compile(r"\.(bmp|jpg|jpeg|png|dds|ogg|ani|scr|tga|slk|xml|txt)$", re.I)


def lua_strings(data):
    """Yield string constants from a Lua 5.0 constant table.

    Layout observed in this client: 0x04 marks a string, followed by a u32
    length and that many bytes. 0x03 marks a double (8 bytes) and 0x01 a
    boolean. Walking with those in mind keeps the scan from drifting into the
    middle of a payload and inventing values.
    """
    i, n = 0, len(data)
    while i < n - 5:
        tag = data[i]
        if tag == 0x04:
            ln = int.from_bytes(data[i + 1:i + 5], "little")
            if 1 <= ln <= 400 and i + 5 + ln <= n:
                raw = data[i + 5:i + 5 + ln]
                if all(32 <= b < 127 or b == 0 for b in raw):
                    yield raw.rstrip(b"\x00").decode("latin1")
                    i += 5 + ln
                    continue
        elif tag == 0x03:
            i += 9
            continue
        i += 1


def main():
    files = sorted(glob.glob(os.path.join(NDADATA, "*.idd")))
    if not files:
        sys.exit("no ndadata .idd files — is extracted/ present?")

    per_file = {}
    all_paths = collections.Counter()
    lua_files = 0

    for path in files:
        with open(path, "rb") as fh:
            data = fh.read()
        if data[:4] != LUA_SIG:
            continue
        lua_files += 1
        found = set()
        for s in lua_strings(data):
            if not s or len(s) < 4:
                continue
            # keep real asset references only: a named basename plus either a
            # known extension or a directory component (rejects a bare ".jpg")
            base = s.rsplit("/", 1)[-1]
            if not base or base.startswith("."):
                continue
            if ASSET_RE.search(s) or ("/" in s and "." in base):
                found.add(s)
        if found:
            per_file[os.path.basename(path)[:-4]] = sorted(found)
            all_paths.update(found)

    payload = {
        "source": "ndadata/*.idd Lua 5.0 string constants",
        "lua_files": lua_files,
        "files_scanned": len(files),
        "unique_paths": len(all_paths),
        "extensions": dict(collections.Counter(
            os.path.splitext(p)[1].lower() for p in all_paths).most_common()),
        "paths": sorted(all_paths),
        "by_bundle": per_file,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(payload, fh, indent=1)

    print(f"scanned        : {len(files)} ndadata bundles")
    print(f"Lua bytecode   : {lua_files}")
    print(f"bundles w/names: {len(per_file)}")
    print(f"unique paths   : {len(all_paths)}")
    print(f"extensions     : {payload['extensions']}")
    print(f"output         : {OUT}")
    for p in payload["paths"][:8]:
        print("   ", p)


if __name__ == "__main__":
    main()
