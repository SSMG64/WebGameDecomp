# wasm pipeline

## Requirements

- WABT (`wasm2wat`, `wasm-objdump`) on your `PATH`
- A compiler that targets `wasm32`: `clang --target=wasm32`, Emscripten's
  `emcc`, or `rustc` with `rustup target add wasm32-unknown-unknown`

## Step by step

**1. Get the target's wasm file onto disk**, somewhere under `local/`
(never a tracked path). Most browser games either fetch a `.wasm` file
directly (visible in your browser's network tab) or embed one as a
base64 blob in a JS file; extract it to its own `.wasm` file first.

**2. Identify the toolchain.**

```
python wasm/tools/split_functions.py --identify local/game.wasm
```

This prints the module's custom sections. Look for a `producers` section,
most C/C++/Rust toolchains embed one naming the exact compiler and SDK
version. Write down whatever you find in `targets/<game>/target.yaml`
under `notes`. This is the single most useful step in the whole process:
guessing at compiler flags without it can cost you far more time than
finding the real toolchain up front.

**3. Split the target.**

```
python wasm/tools/split_functions.py local/game.wasm
```

This writes one `.bytes` file per function under `wasm/dump/functions/`
and seeds `wasm/functions.yaml` with an entry per function: its index,
name (if the module kept a name section), instruction count, and a
hash.

**4. Pick a function and write a candidate.**

Start with small, self-contained functions, math helpers, checksum or
hash routines, string length calculations, before anything that touches
game state or calls many other functions. Copy `wasm/src/TEMPLATE.c` to
a real filename and write your best guess.

**5. Build your whole candidate tree.**

This is the part that differs most from native decomp: build your entire
`wasm/src/` directory into one `.wasm` binary with the toolchain and
flags you identified in step 2, not just the one function you're working
on. Whole-program wasm toolchains optimize across function boundaries,
so an isolated single-function compile is unlikely to reproduce what the
real build does.

**6. Diff.**

```
python wasm/tools/match.py build/candidate.wasm --index 42
```

This re-splits your build the same way it split the target, finds
function 42, and diffs its instructions against the target's dump. You
get a percentage and, if it's not 100%, a unified diff of the
instruction listings. It also updates `wasm/functions.yaml` with the new
status and ratio.

**7. Check overall progress.**

```
python tools/common/progress.py
```

## Reading the diff

A `wasm-objdump` line looks like:

```
000127: 20 00                      | local.get 0
```

The diff tool compares the hex byte column, not the offset or the
mnemonic text, so a match means byte-identical code, full stop. Common
causes of a near-miss:

- **Operand order swapped** (`local.get 1` / `local.get 0` reversed):
  usually means your function's arguments or a binary operator's operands
  are in the wrong order.
- **Extra or missing instructions at the start or end**: often a sign
  the real function does (or doesn't) do bounds checking, null checks, or
  reference counting that your version skips or adds.
- **A whole different opcode where you'd expect a similar one** (`i32.add`
  vs `i32.or`, say): check you're implementing the right operator, and
  check integer signedness, wasm has separate signed/unsigned variants
  for several operations.
- **Ratio stuck around 90 to 95%** with scattered small diffs: often an
  optimization level mismatch (try `-O2` vs `-Os` vs `-O3`) rather than
  anything wrong with your logic.
