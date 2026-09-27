# Contributing conventions

These matter more once more than one person is working on the same
target; for a solo project treat them as good habits rather than rules.

## Status values

Every `functions.yaml` entry uses the same four statuses:

- `not_started`: split out, nobody's written a candidate yet
- `wip`: someone's working on it, match ratio below 0.8
- `close`: match ratio 0.8 or above, not yet exact
- `matching`: byte-identical (wasm/PHP) or an accepted-as-final normalized
  match (js/ts/svelte)

The match tools set these automatically; you generally shouldn't hand-edit
a `status` or `match_ratio` field.

## Picking a function to work on

Prefer functions with few or no calls to other not-yet-matched functions;
matching a leaf function first, then working outward, avoids the
frustration of matching a function whose correctness you can't fully
verify because it calls into something still unmatched.

Two people shouldn't work the same function at once. If you're
coordinating over chat or a shared board, calling a function out as "I'm
on this" before starting saves a lot of duplicated effort.

## Commit hygiene

- Never commit anything under `local/`, `wasm/dump/`, `php/dump/`, or
  `js/dump/`. The `.gitignore` in this template already covers these; if
  your git client shows one of them as a pending change, stop and check
  why before committing.
- One function (or a small, related group) per commit, with the function
  name in the message, keeps `git blame` and review useful as the project
  grows.
- If you change `targets/<game>/target.yaml`, explain what you learned
  and how in the commit message; that file is the project's shared
  memory of what's already been figured out.

## Naming candidate files

Match the target's own name when one exists (a wasm export, a named PHP
function, a variable-assigned JS function). For anonymous wasm functions,
use the index-based name split_functions.py already gave it until you
understand it well enough to rename it meaningfully, then update both the
filename and the `name` field in `functions.yaml` together.
