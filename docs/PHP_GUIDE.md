# PHP pipeline

Zend opcodes are PHP's equivalent of wasm bytecode or native assembly:
a deterministic, versioned output of the PHP compiler that you can dump
and diff. This pipeline uses the `vld` (Vulcan Logic Disassembler)
extension to get at them.

## Building vld

`vld` isn't packaged for most distros, so build it from source. `setup.sh`
does this automatically; by hand it's:

```
git clone https://github.com/derickr/vld.git
cd vld
phpize
./configure
make
sudo make install
```

`make install` places `vld.so` in your PHP's extension directory. You
don't need to edit `php.ini`: every tool in this pipeline loads it
explicitly with `-d extension=vld.so`, passed as `--vld-ext` if yours
lives somewhere non-standard.

Confirm it loaded:

```
php -d extension=vld.so -m | grep vld
```

## Step by step

**1. Get the target PHP source onto disk** under `local/`. If it's
encoded (ionCube, Zend Guard, or a similar loader many old browser-game
server packages used), decode it first with whatever tool matches that
encoder; this pipeline needs plain PHP source to dump opcodes from.

**2. Split the target.**

```
python php/tools/split_functions.py local/game.php
```

This runs the file through `vld` with execution disabled, and saves one
opcode listing per function under `php/dump/functions/`, plus a
`__main__` entry for any top-level file code. `php/functions.yaml` gets
one entry per function with a line count and hash.

**3. Write a candidate.** Copy `php/src/TEMPLATE.php` to a real filename.
Local variable names don't need to match the original: opcodes reference
variables by compiled slot (`!0`, `!1`, ...), not by name, and the
matcher already normalizes that line before comparing.

**4. Diff.**

```
python php/tools/match.py php/src/calculate_damage.php --name calculateDamage
```

This runs your candidate through the same `vld` dump and compares it
against the target's saved opcodes. A mismatch anywhere in the
instruction table, a different opcode, a missing branch, an extra
temporary, shows up in the diff.

## Matching the PHP version

Opcode shapes can shift between PHP major and minor versions (new
opcodes get added, existing ones get restructured) even when the source
looks identical. Match the target's PHP version as closely as you can;
if you don't know it, common tells include:
- error message wording and formatting, which changed across 7.x and 8.x
- syntax that only works on newer versions (named arguments, enums,
  readonly properties, match expressions all set a floor on the version)
- date stamps or comments in any accompanying deployment files

Record whatever you determine in `targets/<game>/target.yaml` under
`php.php_version`.
