# js / ts / svelte pipeline

This one covers plain JavaScript, TypeScript, and Svelte candidates,
because all three eventually become JS text, which is what actually gets
compared. It's a best-effort match, not a byte match; read
`docs/METHODOLOGY.md` first for why.

## Step by step

**1. Get the target bundle onto disk** under `local/`.

**2. Check for a leaked source map first.** This is worth doing before
anything else:

```
node js/tools/recover_sourcemap.js local/game.js
```

Some production builds ship a source map with the original source still
embedded (`sourcesContent`). If that's the case here, this recovers the
literal original files into `js/dump/recovered/`, no candidate writing,
no matching, you already have it. If the map only has file names and
positions but not content, you at least get the original file layout and
names for free, which is still useful context for the next steps.

**3. Get a readable first pass.**

```
node js/tools/deobfuscate.js local/game.js js/dump
```

This runs [webcrack](https://github.com/j4k0xb/webcrack) over the
bundle: unpacking webpack/browserify modules, restoring string literals,
simplifying control flow. It's for your reading, not for the repo, and
it's the input to the next step.

**4. Split into functions.**

```
node js/tools/split_functions.js js/dump/<webcrack output>.js
```

This walks the top-level of the file webcrack produced, records one
`functions.yaml` entry per function it finds (name, size, hash), saves
its text to `js/dump/functions/<name>.original.js`, and drops a stub at
`js/src/<name>.js`.

**5. Write a candidate**, in whichever language fits what you're
reconstructing:

- `js/src/<name>.js` for plain JS
- `js/src/<name>.ts` if you want type annotations while you work; it's
  transpiled with `tsc` before comparison
- `js/src/<name>.svelte` if the target was built with Svelte; it's run
  through the real Svelte compiler before comparison

`match.js` picks whichever of the three exists, in that order, so keep
only one per function.

**6. Diff.**

```
node js/tools/match.js <name> js/dump/functions/<name>.original.js
```

By default this compares your compiled candidate directly against the
reference text. Add `--minify` if you've identified the exact minifier
and settings that produced the raw original bundle and are chasing a
true byte match against a slice of that file instead of against
webcrack's cleaned output; see `docs/METHODOLOGY.md` for when that's
worth attempting.

## Svelte specifics

Svelte's compiled output has a distinctive shape: import lines pulling
in `svelte/internal/*`, a wrapper function taking an `$$anchor`
parameter, calls into the runtime for DOM updates. If your reference
text doesn't look like that, your target probably wasn't built with
Svelte, or your reference is hand-cleaned rather than genuine compiler
output, and a `.svelte` candidate will never score well against it no
matter how correct the logic is. Extract the reference slice from the
real bundle output, not from your own mental model of what it should
look like.

## Common causes of a stuck low score

- **Reference isn't genuine compiler output.** Covered above for Svelte;
  the same applies in miniature to TypeScript, hand-formatted JS won't
  match `tsc`'s output as closely as `tsc`'s output matches itself.
- **Wrong minifier or settings in `--minify` mode.** Terser, esbuild, and
  webpack's built-in minifier all produce different output for the same
  input. If your logic is clearly right and the score won't move, try
  swapping the configured bundler in `target.yaml`.
- **Comparing against webcrack's output while trying to byte-match.**
  webcrack restructures and renames; it is not the original's literal
  bytes, so `--minify` mode against a webcrack-cleaned reference will
  never reach 100%. Point `--minify` mode at a slice of the raw original
  bundle instead.
