#!/usr/bin/env python3
"""Aggregate wasm/functions.yaml and js/functions.yaml into an overall progress report."""
import argparse
import pathlib

import yaml

STATUSES = ["matching", "close", "wip", "not_started"]


def load(path):
    p = pathlib.Path(path)
    if not p.exists():
        return []
    data = yaml.safe_load(p.read_text()) or {}
    return data.get("functions") or []


def badge_svg(pct, out):
    color = "#4c1" if pct >= 90 else "#dfb317" if pct >= 40 else "#e05d44"
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="20">'
        '<rect width="70" height="20" fill="#555"/>'
        f'<rect x="70" width="70" height="20" fill="{color}"/>'
        '<text x="35" y="14" fill="#fff" font-family="Verdana" font-size="11" '
        'text-anchor="middle">matching</text>'
        f'<text x="105" y="14" fill="#fff" font-family="Verdana" font-size="11" '
        f'text-anchor="middle">{pct:.1f}%</text>'
        "</svg>"
    )
    pathlib.Path(out).write_text(svg)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wasm", default="wasm/functions.yaml")
    ap.add_argument("--js", default="js/functions.yaml")
    ap.add_argument("--badge", default="progress.svg")
    args = ap.parse_args()

    entries = load(args.wasm) + load(args.js)
    total = len(entries)
    matched = sum(1 for e in entries if e.get("status") == "matching")
    pct = (matched / total * 100) if total else 0.0

    print(f"{matched}/{total} functions matching ({pct:.2f}%)")
    for status in STATUSES:
        n = sum(1 for e in entries if e.get("status", "not_started") == status)
        print(f"  {status:<12} {n}")

    badge_svg(pct, args.badge)


if __name__ == "__main__":
    main()
