# Methodology

## Where this comes from

Matching decompilation is the discipline used by projects like
zeldaret/botw, the sm64 decomp, and MinecraftLCE. You don't just write
code that behaves like the original, you write code that a specific
compiler turns into the exact same bytes. Progress is a mechanically
verified percentage, tracked function by function, not a subjective
"looks about right."

The standard toolchain for that community is `splat` (splits a binary
into per-function assembly), `asm-differ` (diffs candidate vs. target
assembly with a similarity score), `decomp-permuter` (randomly mutates a
candidate until it matches), and `m2c`/`mips2c` (assembly-to-C first
guess). WebGameDecomp adapts the same loop, split, write, compile, diff,
score, to three web targets that don't have off-the-shelf equivalents of
those tools: WebAssembly, PHP, and the JS/TS/Svelte family.

## True matching: wasm and PHP

Two of the three pipelines get a real byte match, because both targets
are the deterministic output of a compiler you can identify and re-run.

**WebAssembly** is a compiler target, same as MIPS or PowerPC. Given the
same compiler, version, and flags, compiling the same source produces the
same bytecode. `wasm-objdump -d` gives you the same kind of per-function,
per-instruction byte listing that `objdump` gives a native decomp
project, which is what `wasm/tools/split_functions.py` parses. The one
real difference from native decomp: compiling a single function in
isolation is less reliable for wasm than for a native `.o` file, because
whole-program toolchains like Emscripten do cross-function optimization.
`wasm/tools/match.py` assumes you build your entire candidate tree with
the target toolchain and diff the resulting binary function by function,
rather than compiling one function alone. Run
`split_functions.py --identify` before writing any source. Most wasm
toolchains embed a `producers` custom section naming the exact compiler
and SDK version, which is worth more than hours of guessing at flags.

**PHP** compiles to Zend opcodes, and the `vld` extension dumps them the
same way `wasm-objdump` dumps wasm instructions. `php/tools/split_functions.py`
runs the target through `vld` and saves one opcode listing per function.
Opcodes reference local variables by compiled slot, not by name, so
`php/tools/match.py` already tolerates renaming a variable; it will still
catch a different operator, a different branch, or an extra temp. The
practical requirement here is matching the target's PHP major/minor
version as closely as you can, since opcode shapes do shift between
versions. See `docs/PHP_GUIDE.md`.

## Best-effort matching: js, ts, and svelte

A minified JS bundle is not the direct output of one compiler invocation
you control. It is usually a pipeline (bundler, then minifier, then
sometimes an obfuscator), any stage of which can be one of several tools,
in any version, with settings that were never published. Reproducing
that pipeline byte-for-byte is sometimes achievable if you can fingerprint
the exact tool, version, and config, but often isn't.

Because of that, `js/tools/match.js` doesn't report a boolean. By
default it compares your candidate's compiled JS directly against your
reference text, and reports a similarity ratio with a diff. Read a high
percentage as "structurally and semantically equivalent," not "verified
identical." Pass `--minify` to instead run your candidate through the
minifier configured in `targets/<game>/target.yaml` before comparing,
for the advanced case where you've identified the original pipeline and
are chasing an actual byte match against a slice of the raw bundle.

TypeScript and Svelte candidates slot into the same pipeline: `match.js`
detects a `.ts` or `.svelte` file under `js/src/` and compiles it to JS
first (via `tsc`'s transpile step, or the Svelte compiler) before running
the same comparison. The one thing worth knowing up front: Svelte's
compiled output has a very distinctive shape (import lines, an
`$$anchor`-taking wrapper function, calls into `svelte/internal`), so it
will only look like your reference text if that reference is itself
genuine Svelte-compiled output, not a hand-written guess at what a
Svelte component "should" compile to. If your target game was built with
Svelte, extract the reference slice from the real bundle. The same logic
applies to TypeScript, just with a much smaller gap between hand-written
JS and `tsc`'s output for simple functions.

Before writing any JS/TS/Svelte candidate, run
`js/tools/recover_sourcemap.js` on the target bundle. Some builds
accidentally ship a source map with `sourcesContent` still attached,
which hands you the literal original file. When that happens, skip the
matching pipeline for that file entirely, there's nothing left to
reconstruct.

## What never gets committed

All three pipelines follow the same rule native decomps use for their
`asm/` directories: raw material extracted from the original
(disassembly, opcode dumps, deobfuscated source, recovered sourcemaps)
lives only in the gitignored `dump/` folders, generated locally from your
own copy. The only things tracked in git are tooling, your own candidate
source, and small metadata (name, size, a hash, a match percentage),
enough to coordinate and show progress without redistributing anyone
else's copyrighted work. See `docs/LEGAL.md`.
