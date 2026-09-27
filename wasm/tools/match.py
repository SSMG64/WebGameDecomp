#!/usr/bin/env python3
"""Diff one function of a candidate build against the target dump.

Build your whole candidate source tree with the same toolchain/flags as
the original (see docs/METHODOLOGY.md for why a single-function compile
isn't reliable for wasm), point this at the resulting .wasm, and it
re-runs the same wasm-objdump split on your build to diff the named
function against wasm/dump/functions/.
"""
import argparse
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "common"))
from byte_diff import diff_instructions, is_exact  # noqa: E402

import split_functions as sf  # noqa: E402


def load_dump(dump_dir, index):
    for f in sorted(pathlib.Path(dump_dir).glob(f"{index:05d}_*.bytes")):
        lines = f.read_text().splitlines()
        return [tuple(line.split("\t")) for line in lines if line.strip()]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate_wasm")
    ap.add_argument("--index", type=int, required=True, help="function index, matching wasm/functions.yaml")
    ap.add_argument("--target-dump", default="wasm/dump/functions")
    ap.add_argument("--manifest", default="wasm/functions.yaml")
    args = ap.parse_args()

    target = load_dump(args.target_dump, args.index)
    if target is None:
        sys.exit(f"no target dump for function {args.index}, run split_functions.py on the original first")

    text = sf.run(["wasm-objdump", "-d", args.candidate_wasm])
    candidate_functions = sf.parse_objdump(text)
    candidate_fn = candidate_functions.get(args.index)
    if candidate_fn is None:
        sys.exit(f"function index {args.index} not found in candidate build")
    candidate = candidate_fn["instructions"]

    if is_exact(target, candidate):
        print(f"function {args.index}: MATCHING (100.00%)")
        status, ratio = "matching", 1.0
    else:
        ratio, diff = diff_instructions(target, candidate)
        status = "close" if ratio >= 0.8 else "wip"
        print(f"function {args.index}: {status.upper()} ({ratio * 100:.2f}%)")
        print("\n".join(diff[:200]))

    manifest_path = pathlib.Path(args.manifest)
    data = yaml.safe_load(manifest_path.read_text()) or {"functions": []}
    for entry in data.get("functions") or []:
        if entry["index"] == args.index:
            entry["status"] = status
            entry["match_ratio"] = round(ratio, 4)
    manifest_path.write_text(yaml.safe_dump(data, sort_keys=False))


if __name__ == "__main__":
    main()
