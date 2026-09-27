#!/usr/bin/env node
// First-pass cleanup of an obfuscated target file, for human reading only.
// Output goes to js/dump/ (gitignored). Never commit this.
import fs from "node:fs";
import { webcrack } from "webcrack";

const [, , input, outDir = "js/dump"] = process.argv;
if (!input) {
    console.error("usage: node deobfuscate.js <obfuscated.js> [outDir]");
    process.exit(1);
}

const code = fs.readFileSync(input, "utf8");
const result = await webcrack(code);
fs.mkdirSync(outDir, { recursive: true });
await result.save(outDir);
console.log(`deobfuscated output written to ${outDir}`);
