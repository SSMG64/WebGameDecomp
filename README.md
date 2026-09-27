# WebGameDecomp

A matching-decompilation scaffold for browser games, modeled on the
workflow used by native-code decomp projects like
[MinecraftLCE](https://github.com/GRAnimated/MinecraftLCE) (itself based
on [zeldaret/botw](https://github.com/zeldaret/botw)), and built on the
same idea popularized by `splat`, `asm-differ`, and `decomp-permuter`:
instead of reading disassembly and writing a best guess, you write source
code and mechanically verify it produces the *same bytes* as the
original.

Three pipelines are included, covering the runtimes most browser games
actually ship in:

- **`wasm/`**: true byte matching. WebAssembly is a compiler target like
  MIPS or PowerPC, so the classic decomp loop transfers directly: compile
  your candidate C/C++/Rust with the same toolchain as the original,
  disassemble both with `wasm-objdump`, and diff function by function.
- **`php/`**: also true matching, at the opcode level. The `vld`
  extension dumps Zend opcodes the way `wasm-objdump` dumps wasm
  instructions, which covers old browser games with server-side PHP
  logic (including ionCube/Zend-encoded titles, once decoded).
- **`js/`**: best-effort matching for JavaScript, TypeScript, and Svelte.
  Obfuscated/minified JS is usually produced by some bundler and
  minifier, but which ones (and with what config) is often unknown, so
  matches are scored as a similarity percentage rather than a strict
  pass/fail. TS and Svelte candidates are compiled down to JS before the
  same comparison runs.

Full docs live in `docs/`, start with `docs/GETTING_STARTED.md`. For the
reasoning behind each pipeline and its limits, see `docs/METHODOLOGY.md`.

## This repo contains no game assets

Like every decomp project it's modeled on, this template never holds the
original binary, bundle, or source, or any text/bytes extracted directly
from them. Those all live under `local/`, `wasm/dump/`, `php/dump/`, and
`js/dump/`, which are gitignored. The only things that get committed are
tooling, your own hand-written candidate source under `*/src/`, and small
metadata files (`functions.yaml`) recording names, sizes, hashes, and
match percentages, never the copyrighted content itself. You need your
own legally obtained copy of whatever you're working on. See
`docs/LEGAL.md`.

## Quick start

```
./setup.sh
```

This installs what it can for all three pipelines (WABT, a wasm32
compiler, PHP plus a locally built `vld`, and the Node dependencies) and
prints a checklist of anything it couldn't set up automatically. Then:

```
cd examples/demo
cat README.md
```

Each pipeline has a trivial, self-contained demo there that needs no
game files at all, just to confirm your local toolchain works before you
point it at anything real. Full setup and workflow details are in
`docs/GETTING_STARTED.md`.

## Layout

```
setup.sh                     installs and checks the toolchain for all three pipelines
targets/<game>/target.yaml   toolchain + bundler config per target
wasm/functions.yaml          status + hashes, one row per function
wasm/src/                    your candidate C/C++/Rust, committed
wasm/dump/                   extracted target bytes, gitignored
wasm/tools/                  split_functions.py, match.py
php/functions.yaml           status + hashes, one row per function
php/src/                     your candidate PHP, committed
php/dump/                    extracted opcode dumps, gitignored
php/tools/                   split_functions.py, match.py
js/functions.yaml            status + hashes, one row per function
js/src/                      your candidate JS/TS/Svelte, committed
js/dump/                     deobfuscated/extracted target text, gitignored
js/tools/                    deobfuscate.js, split_functions.js, match.js, recover_sourcemap.js
tools/common/                shared diff engine and progress/report tool
examples/demo/               trivial self-contained test case per pipeline
docs/                        full documentation, start at docs/GETTING_STARTED.md
```
