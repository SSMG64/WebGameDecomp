# Toolchain sanity checks

No real game files needed here, these confirm each pipeline's tools are
installed and working correctly before you point them at anything real.
Run `../../setup.sh` first if you haven't already.

## wasm

There's no "original" here, `demo.c` is both the target and the
candidate, so it should always match 100%.

```
clang --target=wasm32 -O2 -nostdlib -Wl,--no-entry -Wl,--export-all -o demo.wasm demo.c
python ../../wasm/tools/split_functions.py demo.wasm --dump-dir dump --manifest manifest.yaml
python ../../wasm/tools/match.py demo.wasm --index 1 --target-dump dump --manifest manifest.yaml
```

Expected: `function 1: MATCHING (100.00%)` (index 1 is the `add`
function; index 0 is a compiler-generated constructor stub).

## php

```
python ../../php/tools/split_functions.py demo.php --dump-dir php-dump --manifest php-manifest.yaml
python ../../php/tools/match.py demo.php --name add --target-dump php-dump --manifest php-manifest.yaml
```

Expected: `add: MATCHING (100.00%)`.

If this fails with a message about the `vld` extension not being found,
follow `docs/PHP_GUIDE.md` to build it.

## js / ts

```
cd js
node ../../../js/tools/match.js add target.js . manifest.yaml
```

Expected: `MATCHING (100.00%)`. This resolves `add.ts`, transpiles it
with `tsc`, and compares the result against `target.js`. Try editing
`add.ts` to change the logic and re-run to see a non-matching diff.
