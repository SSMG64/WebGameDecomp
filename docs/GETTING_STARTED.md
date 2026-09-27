# Getting started

## 1. Install dependencies

Run the setup script from the repo root:

```
./setup.sh
```

It installs what it can (wabt, a wasm32 clang target, Node packages, PHP
plus a locally-built `vld` extension) and prints a checklist of what's
missing so you can install it by hand if your platform needs a different
package manager. It's safe to re-run any time.

If you'd rather install by hand, or `setup.sh` doesn't support your
platform, here's the full list:

| Tool | Used by | Typical install |
|---|---|---|
| Python 3.10+ | all `*.py` tools | usually already installed |
| `pip install -r requirements.txt` | all `*.py` tools | run from repo root |
| Node 18+ | all `*.js` tools | [nodejs.org](https://nodejs.org) |
| `npm install` | all `*.js` tools | run from repo root |
| WABT (`wasm2wat`, `wasm-objdump`) | wasm pipeline | `apt install wabt`, `brew install wabt` |
| A wasm32-capable compiler | wasm pipeline | `apt install clang lld`, or Emscripten |
| PHP 8.x CLI + `php-dev` | php pipeline | `apt install php-cli php-dev`, `brew install php` |
| `vld` extension | php pipeline | built from source, see `docs/PHP_GUIDE.md` |

## 2. Run the demos

Each pipeline has a self-contained demo under `examples/demo/` that needs
no game files at all, just to confirm your local toolchain works before
you point it at anything real:

```
cd examples/demo
cat README.md
```

Follow that file for all three: wasm, php, and js/ts/svelte. You should
see `MATCHING (100.00%)` from each one.

## 3. Set up your first real target

1. Copy `targets/example-game/target.yaml` to `targets/<your-game>/target.yaml`
   and fill in what you know.
2. Put your own legally obtained copy of the game's files under `local/`.
   This directory is gitignored and should never be committed.
3. Pick the pipeline that matches what you're reverse engineering:
   - a `.wasm` file: `docs/WASM_GUIDE.md`
   - minified/obfuscated JS, TS, or a Svelte-built bundle: `docs/JS_GUIDE.md`
   - PHP source, including ionCube/Zend-encoded PHP you've already decoded: `docs/PHP_GUIDE.md`
4. Run `tools/common/progress.py` any time to see your overall percentage
   across every pipeline you're using for that game.

## 4. A sane per-function workflow

Whichever pipeline you're using, the loop is the same:

1. Split the target into per-function reference data.
2. Pick one function from its `functions.yaml`.
3. Write your best guess in `<pipeline>/src/`.
4. Run the matching tool. Read the diff. Adjust. Repeat.
5. Once it's `matching`, move to the next function.

Work on small, low-dependency functions first (math helpers, string
utilities) before tackling anything that touches game state. It's the
same advice every native decomp project gives new contributors, and it
holds here too.
