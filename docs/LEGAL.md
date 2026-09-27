# What this repo holds, and what it doesn't

This is a template for a decompilation project, not a decompilation of
anything in particular. It ships with:

- tooling (the Python and Node scripts under `wasm/`, `php/`, `js/`,
  `tools/`)
- a trivial, original demo (`examples/demo/`) used only to sanity-check
  that your local toolchain works
- empty templates and schema examples (`*/src/TEMPLATE.*`,
  `*/functions.yaml`)

It never holds, and is deliberately set up (via `.gitignore`) to make it
hard to accidentally commit:

- the original game binary, bundle, or source, in any form
- disassembly, opcode dumps, or deobfuscated text extracted from it
- anything recovered via `js/tools/recover_sourcemap.js`

The only things a real project built from this template should commit
are: your own hand-written candidate reimplementations, the tooling, and
small metadata (`functions.yaml`: names, sizes, hashes, match
percentages). This mirrors the convention every native-code matching
decomp project (BOTW, Odyssey, Mario 64, MinecraftLCE, and others) uses
for the same reason: the point of a matching decomp is to publish
original, independently written source that happens to compile to the
same output, not to redistribute someone else's copyrighted work.

## Before you start on a real target

You need your own legal access to whatever you're studying, the same
bar that applies to any of the native decomp projects this template is
modeled on. This tooling doesn't help you obtain a game, bypass access
controls, or distribute anything you don't have the rights to; it helps
you write and verify your own reimplementation of logic you already have
lawful access to.

This project doesn't offer legal advice. If you're planning to publish a
decomp of a specific commercial game, the norms and risks (and how
individual rightsholders have historically responded) vary a lot by game
and by jurisdiction; look at how comparable existing projects in that
specific ecosystem have handled it, and if it matters to you, talk to
someone qualified before you publish.
