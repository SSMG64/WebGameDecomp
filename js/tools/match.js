#!/usr/bin/env node
// Scores a candidate (.js, .ts, or .svelte) against a reference slice.
// Default: direct normalized comparison. --minify: run through the
// configured minifier first. See docs/JS_GUIDE.md.
import fs from "node:fs";
import path from "node:path";
import { createTwoFilesPatch, diffWords } from "diff";
import yaml from "js-yaml";
import * as terser from "terser";

const CANDIDATE_EXTS = ["ts", "svelte", "js"];

function resolveCandidate(srcDir, name) {
    for (const ext of CANDIDATE_EXTS) {
        const candidatePath = path.join(srcDir, `${name}.${ext}`);
        if (fs.existsSync(candidatePath)) return { path: candidatePath, ext };
    }
    return null;
}

async function toJS(candidate) {
    const src = fs.readFileSync(candidate.path, "utf8");
    if (candidate.ext === "js") return src;

    if (candidate.ext === "ts") {
        const ts = await import("typescript");
        const out = ts.transpileModule(src, {
            compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 },
        });
        return out.outputText;
    }

    if (candidate.ext === "svelte") {
        const { compile } = await import("svelte/compiler");
        const result = compile(src, { filename: candidate.path, generate: "client" });
        return result.js.code;
    }

    throw new Error(`unsupported candidate extension: ${candidate.ext}`);
}

const args = process.argv.slice(2).filter((a) => a !== "--minify");
const doMinify = process.argv.includes("--minify");
const [name, targetSlicePath, srcDir = "js/src", manifestPath = "js/functions.yaml"] = args;

if (!name || !targetSlicePath) {
    console.error("usage: node match.js <functionName> <reference-slice.js> [srcDir] [manifestPath] [--minify]");
    console.error("reference-slice.js: usually js/dump/functions/<name>.original.js from split_functions.js");
    console.error("candidate: js/src/<name>.js, .ts, or .svelte, whichever exists");
    process.exit(1);
}

const candidate = resolveCandidate(srcDir, name);
if (!candidate) {
    console.error(`no candidate found at ${srcDir}/${name}.{js,ts,svelte}`);
    process.exit(1);
}

const candidateJS = await toJS(candidate);
const targetSrc = fs.readFileSync(targetSlicePath, "utf8");

let candidateOut = candidateJS.trim();
if (doMinify) {
    const minified = await terser.minify(candidateJS, { compress: true, mangle: true });
    candidateOut = (minified.code || "").trim();
}
const targetOut = targetSrc.trim();

const normalize = (s) => s.replace(/\s+/g, " ").trim();
const exact = normalize(candidateOut) === normalize(targetOut);

const parts = diffWords(normalize(targetOut), normalize(candidateOut));
const changed = parts.filter((p) => p.added || p.removed).reduce((n, p) => n + p.value.length, 0);
const totalLen = normalize(targetOut).length || 1;
const ratio = exact ? 1 : Math.max(0, 1 - changed / totalLen);

console.log(exact ? "MATCHING (100.00%)" : `${ratio >= 0.8 ? "CLOSE" : "WIP"} (${(ratio * 100).toFixed(2)}%)`);
if (!exact) {
    console.log(createTwoFilesPatch("target", "candidate", targetOut, candidateOut));
}

let manifest = { functions: [] };
if (fs.existsSync(manifestPath)) {
    manifest = yaml.load(fs.readFileSync(manifestPath, "utf8")) || { functions: [] };
}
for (const entry of manifest.functions || []) {
    if (entry.name === name) {
        entry.status = exact ? "matching" : ratio >= 0.8 ? "close" : "wip";
        entry.match_ratio = Number(ratio.toFixed(4));
    }
}
fs.writeFileSync(manifestPath, yaml.dump(manifest, { sortKeys: false }));
