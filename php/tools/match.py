#!/usr/bin/env python3
"""Diff a candidate PHP function's opcodes against the target dump.

Because Zend opcodes reference variables by compiled slot, not by name,
this comparison is already tolerant of local variable renaming. Anything
else that differs (a different operator, a different branch, an extra
temp) will show up in the diff.
"""
import argparse
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "common"))
from byte_diff import diff_lines  # noqa: E402

import split_functions as sf  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate_php")
    ap.add_argument("--name", required=True, help="function name, or __main__ for top-level file code")
    ap.add_argument("--target-dump", default="php/dump/functions")
    ap.add_argument("--manifest", default="php/functions.yaml")
    ap.add_argument("--php-bin", default="php")
    ap.add_argument("--vld-ext", default="vld.so")
    args = ap.parse_args()

    safe = pathlib.Path(args.name.replace("/", "_"))
    target_file = pathlib.Path(args.target_dump) / f"{safe}.opcodes"
    if not target_file.exists():
        sys.exit(f"no target dump for {args.name}, run split_functions.py on the original first")
    target_lines = target_file.read_text().splitlines()

    output = sf.run_vld(args.candidate_php, args.php_bin, args.vld_ext)
    blocks = sf.parse_vld(output)
    if args.name not in blocks:
        sys.exit(f"function {args.name} not found in candidate output")
    candidate_lines = sf.clean_block(blocks[args.name])

    ratio, diff = diff_lines(target_lines, candidate_lines)
    status = "matching" if ratio == 1.0 else "close" if ratio >= 0.8 else "wip"
    print(f"{args.name}: {status.upper()} ({ratio * 100:.2f}%)")
    if ratio < 1.0:
        print("\n".join(diff[:200]))

    manifest_path = pathlib.Path(args.manifest)
    data = yaml.safe_load(manifest_path.read_text()) or {"functions": []}
    for entry in data.get("functions") or []:
        if entry["name"] == args.name:
            entry["status"] = status
            entry["match_ratio"] = round(ratio, 4)
    manifest_path.write_text(yaml.safe_dump(data, sort_keys=False))


if __name__ == "__main__":
    main()
