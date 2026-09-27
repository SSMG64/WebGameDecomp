#!/usr/bin/env node
// Walk a deobfuscated file and record one manifest entry per top-level
// function, plus a fill-in-the-blank stub under js/src/. The original
// text stays under js/dump/ (gitignored); only stubs and metadata
// (name, size, hash) get committed.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import * as acorn from "acorn";
import yaml from "js-yaml";

const [, , input, srcDir = "js/src", dumpDir = "js/dump/functions", manifestPath = "js/functions.yaml"] = process.argv;
if (!input) {
    console.error("usage: node split_functions.js <deobfuscated.js> [srcDir] [dumpDir] [manifestPath]");
    process.exit(1);
}

const code = fs.readFileSync(input, "utf8");
const ast = acorn.parse(code, { ecmaVersion: "latest", sourceType: "module", locations: true });

function functionName(node, index) {
    if (node.id) return node.id.name;
    if (node.type === "VariableDeclaration") {
        const d = node.declarations[0];
        if (d && d.id && d.id.name) return d.id.name;
    }
    return `anon_${index}`;
}

const found = [];
ast.body.forEach((node, index) => {
    const isFunc = node.type === "FunctionDeclaration";
    const isVarFunc =
        node.type === "VariableDeclaration" &&
        node.declarations[0] &&
        node.declarations[0].init &&
        ["FunctionExpression", "ArrowFunctionExpression"].includes(node.declarations[0].init.type);
    if (!isFunc && !isVarFunc) return;

    const name = functionName(node, index);
    const slice = code.slice(node.start, node.end);
    const sha256 = crypto.createHash("sha256").update(slice).digest("hex");
    found.push({ name, slice, sha256, chars: slice.length });
});

fs.mkdirSync(srcDir, { recursive: true });
fs.mkdirSync(dumpDir, { recursive: true });
for (const fn of found) {
    fs.writeFileSync(path.join(dumpDir, `${fn.name}.original.js`), fn.slice);
}
for (const fn of found) {
    const stubPath = path.join(srcDir, `${fn.name}.js`);
    if (!fs.existsSync(stubPath)) {
        const stub =
            `// candidate reimplementation of "${fn.name}"\n` +
            `// original: ${fn.chars} chars, sha256 ${fn.sha256.slice(0, 12)}...\n` +
            `function ${fn.name}() {\n    throw new Error("not implemented");\n}\n\n` +
            `export default ${fn.name};\n`;
        fs.writeFileSync(stubPath, stub);
    }
}

let manifest = { functions: [] };
if (fs.existsSync(manifestPath)) {
    manifest = yaml.load(fs.readFileSync(manifestPath, "utf8")) || { functions: [] };
}
const byName = new Map((manifest.functions || []).map((e) => [e.name, e]));
for (const fn of found) {
    const entry = byName.get(fn.name) || {
        name: fn.name,
        status: "not_started",
        source: `js/src/${fn.name}.js`,
        match_ratio: 0,
    };
    entry.sha256 = fn.sha256;
    entry.original_chars = fn.chars;
    byName.set(fn.name, entry);
}
manifest.functions = [...byName.values()];
fs.writeFileSync(manifestPath, yaml.dump(manifest, { sortKeys: false }));
console.log(`found ${found.length} functions, stubs in ${srcDir}, manifest at ${manifestPath}`);
