#!/usr/bin/env python3
"""Split a PHP file into per-function Zend opcode dumps using the VLD extension.

Point this only at your own local copy. Output goes to a dump directory
that should stay gitignored, since it's derived directly from the
original file.
"""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

import yaml

FUNC_START = re.compile(r"^Function (\S+):$")
END_MARK = "End of function "
COMPILED_VARS = re.compile(r"^(compiled vars:\s*)(.*)$")
VAR_NAME = re.compile(r"\s*=\s*\$\w+")


def normalize_compiled_vars(line):
    m = COMPILED_VARS.match(line)
    if not m:
        return line
    prefix, rest = m.groups()
    return prefix + VAR_NAME.sub("", rest)


def run_vld(php_file, php_bin="php", vld_ext="vld.so"):
    cmd = [php_bin, "-d", f"extension={vld_ext}", "-dvld.active=1", "-dvld.execute=0", php_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stderr


def parse_vld(output):
    lines = output.splitlines()
    blocks = {}

    i = 0
    top_level = []
    while i < len(lines) and not FUNC_START.match(lines[i]):
        top_level.append(lines[i])
        i += 1
    if any(line.strip() for line in top_level):
        blocks["__main__"] = top_level

    while i < len(lines):
        m = FUNC_START.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        i += 1
        body = []
        while i < len(lines) and not lines[i].startswith(END_MARK):
            body.append(lines[i])
            i += 1
        blocks[name] = body
        i += 1

    return blocks


def clean_block(body):
    out, started = [], False
    for line in body:
        if line.startswith("filename:"):
            started = True
            continue
        if started:
            out.append(normalize_compiled_vars(line))
    return out or body


def write_function(dump_dir, name, lines):
    safe = re.sub(r"[^\w.-]", "_", name)
    out = dump_dir / f"{safe}.opcodes"
    text = "\n".join(lines)
    out.write_text(text + "\n")
    sha = hashlib.sha256(text.encode()).hexdigest()
    return out.name, len(lines), sha


def update_manifest(manifest_path, discovered):
    data = {"functions": []}
    if manifest_path.exists():
        data = yaml.safe_load(manifest_path.read_text()) or {"functions": []}

    existing = {e["name"]: e for e in data.get("functions") or []}
    for name, (file_name, count, sha) in discovered.items():
        entry = existing.get(name, {"name": name, "status": "not_started", "source": None, "match_ratio": 0.0})
        entry.update({"line_count": count, "sha256": sha, "dump_file": file_name})
        existing[name] = entry

    data["functions"] = sorted(existing.values(), key=lambda e: e["name"])
    manifest_path.write_text(yaml.safe_dump(data, sort_keys=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("php_file")
    ap.add_argument("--dump-dir", default="php/dump/functions")
    ap.add_argument("--manifest", default="php/functions.yaml")
    ap.add_argument("--php-bin", default="php")
    ap.add_argument("--vld-ext", default="vld.so")
    args = ap.parse_args()

    output = run_vld(args.php_file, args.php_bin, args.vld_ext)
    if "function name:" not in output:
        sys.exit("no VLD output found, is the vld extension built? see docs/PHP_GUIDE.md")

    blocks = parse_vld(output)
    if not blocks:
        sys.exit("no functions parsed from VLD output")

    dump_dir = pathlib.Path(args.dump_dir)
    dump_dir.mkdir(parents=True, exist_ok=True)
    discovered = {name: write_function(dump_dir, name, clean_block(body)) for name, body in blocks.items()}
    update_manifest(pathlib.Path(args.manifest), discovered)
    print(f"split {len(discovered)} functions into {dump_dir}")


if __name__ == "__main__":
    main()
