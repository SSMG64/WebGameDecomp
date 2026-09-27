#!/usr/bin/env python3
"""Split a wasm binary into per-function disassembly using wabt's wasm-objdump.

Point this only at your own local copy, never a tracked file. Output
goes to a dump directory that should stay gitignored, since it's derived
directly from the original binary.
"""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

import yaml

FUNC_HEADER = re.compile(r"^[0-9a-f]+\s+func\[(\d+)\](?:\s+<([^>]+)>)?:")
INSTR_LINE = re.compile(r"^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s?)+)\s*\|\s*(.*)$")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def parse_objdump(text):
    functions = {}
    current = None
    for line in text.splitlines():
        m = FUNC_HEADER.match(line)
        if m:
            idx, name = m.group(1), m.group(2)
            current = {"index": int(idx), "name": name, "instructions": []}
            functions[int(idx)] = current
            continue
        m = INSTR_LINE.match(line)
        if m and current is not None:
            offset, hexb, text_ = m.groups()
            current["instructions"].append((offset, hexb.strip(), text_.strip()))
    return functions


def write_function(dump_dir, index, fn):
    name = fn["name"] or f"func_{index}"
    safe = re.sub(r"[^\w.-]", "_", name)
    out = dump_dir / f"{index:05d}_{safe}.bytes"
    lines = [f"{off}\t{hexb}\t{txt}" for off, hexb, txt in fn["instructions"]]
    out.write_text("\n".join(lines) + "\n" if lines else "")

    blob = "".join(hexb.replace(" ", "") for _, hexb, _ in fn["instructions"])
    sha = hashlib.sha256(bytes.fromhex(blob)).hexdigest() if blob else ""
    return out.name, len(fn["instructions"]), sha, name


def update_manifest(manifest_path, discovered):
    data = {"functions": []}
    if manifest_path.exists():
        data = yaml.safe_load(manifest_path.read_text()) or {"functions": []}

    existing = {e["index"]: e for e in data.get("functions") or []}
    for index, (file_name, count, sha, name) in discovered.items():
        entry = existing.get(index, {"index": index, "status": "not_started", "source": None, "match_ratio": 0.0})
        entry.update({"name": name, "instruction_count": count, "sha256": sha, "dump_file": file_name})
        existing[index] = entry

    data["functions"] = sorted(existing.values(), key=lambda e: e["index"])
    manifest_path.write_text(yaml.safe_dump(data, sort_keys=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wasm_file")
    ap.add_argument("--dump-dir", default="wasm/dump/functions")
    ap.add_argument("--manifest", default="wasm/functions.yaml")
    ap.add_argument(
        "--identify",
        action="store_true",
        help="print the module's custom sections (producers, target_features, etc.) and exit",
    )
    args = ap.parse_args()

    if args.identify:
        try:
            print(run(["wasm-objdump", "-x", args.wasm_file]))
        except FileNotFoundError:
            sys.exit("wasm-objdump not found, install the WebAssembly Binary Toolkit (wabt)")
        return

    dump_dir = pathlib.Path(args.dump_dir)
    dump_dir.mkdir(parents=True, exist_ok=True)

    try:
        text = run(["wasm-objdump", "-d", args.wasm_file])
    except FileNotFoundError:
        sys.exit("wasm-objdump not found, install the WebAssembly Binary Toolkit (wabt)")

    functions = parse_objdump(text)
    if not functions:
        sys.exit("no functions parsed, is this a valid wasm binary with a Code section?")

    discovered = {i: write_function(dump_dir, i, fn) for i, fn in functions.items()}
    update_manifest(pathlib.Path(args.manifest), discovered)
    print(f"split {len(discovered)} functions into {dump_dir}")


if __name__ == "__main__":
    main()
