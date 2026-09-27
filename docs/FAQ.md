# FAQ / troubleshooting

**`wasm-objdump: command not found`**
Install WABT: `apt install wabt`, `brew install wabt`, or build from
[WebAssembly/wabt](https://github.com/WebAssembly/wabt).

**`clang: error: unknown target triple 'wasm32'`**
Your clang build doesn't include the wasm32 backend. On Ubuntu,
`apt install clang lld` from a recent release should include it; if not,
use Emscripten's `emcc` instead and adjust `compile_cmd` in `target.yaml`.

**`no VLD output found, is the vld extension built?`**
Confirm it built and is visible: `php -d extension=vld.so -m | grep vld`.
If that's empty, rebuild following `docs/PHP_GUIDE.md`, and double-check
`--vld-ext` points at the actual `.so` path if it isn't on PHP's default
extension path.

**A wasm function matches 0% no matter what I write**
Check you're comparing the right index; module optimization can renumber
functions between builds. Re-run `split_functions.py --identify` and
confirm the toolchain in `target.yaml` still matches, and make sure
you're diffing your *whole build's* output, not a single function
compiled in isolation (see `docs/WASM_GUIDE.md`).

**A JS/TS/Svelte match won't get above 90% even though the logic looks right**
See "Common causes of a stuck low score" in `docs/JS_GUIDE.md`. The short
version: check whether your reference text is genuine compiler output
for the language you're using, and whether `--minify` mode is configured
with the right bundler.

**PHP opcodes differ only in variable order or numbering**
This usually means the number or order of parameters or locals differs
subtly (an unused variable, a parameter you dropped), not that anything
is semantically wrong elsewhere. The diff output will point at exactly
which slot changed.

**Where do I actually get the target's `.wasm` or `.js` file from?**
Your browser's network tab, viewed while playing the game, is usually
the easiest way: filter by file type and save the response body. This
toolbox assumes you already have your own legal access to whatever
you're working on; see `docs/LEGAL.md`.

**Can I use this on a game I don't own or haven't obtained legitimately?**
No. See `docs/LEGAL.md`.
