#!/usr/bin/env node
// Pulls original sources out of a leaked sourcemap, if sourcesContent is
// present. Output goes to js/dump/recovered/ (gitignored). See docs/JS_GUIDE.md.
import fs from "node:fs";
import path from "node:path";

const [, , input, outDir = "js/dump/recovered"] = process.argv;
if (!input) {
    console.error("usage: node recover_sourcemap.js <bundle.js or bundle.js.map> [outDir]");
    process.exit(1);
}

function loadMap(input) {
    if (input.endsWith(".map")) {
        return JSON.parse(fs.readFileSync(input, "utf8"));
    }

    const bundle = fs.readFileSync(input, "utf8");
    const inlineMatches = [...bundle.matchAll(/\/\/[#@]\s*sourceMappingURL=data:application\/json;(?:charset=[^;]+;)?base64,(\S+)/g)];
    if (inlineMatches.length) {
        const b64 = inlineMatches[inlineMatches.length - 1][1];
        return JSON.parse(Buffer.from(b64, "base64").toString("utf8"));
    }

    const urlMatches = [...bundle.matchAll(/\/\/[#@]\s*sourceMappingURL=(\S+)/g)];
    const urlMatch = urlMatches[urlMatches.length - 1];
    if (urlMatch && !urlMatch[1].startsWith("data:")) {
        const mapPath = path.join(path.dirname(input), urlMatch[1]);
        if (fs.existsSync(mapPath)) {
            return JSON.parse(fs.readFileSync(mapPath, "utf8"));
        }
        console.error(`bundle references ${urlMatch[1]} but that file was not found next to it`);
    }

    return null;
}

const map = loadMap(input);
if (!map) {
    console.error("no source map found (checked for an inline map and a sourceMappingURL comment)");
    process.exit(1);
}

const sources = map.sources || [];
const contents = map.sourcesContent || [];
console.log(`map lists ${sources.length} source file(s)`);

if (!contents.length || contents.every((c) => c == null)) {
    console.log("no sourcesContent embedded, this map has file names but not the original text:");
    sources.forEach((s) => console.log(`  ${s}`));
    process.exit(0);
}

fs.mkdirSync(outDir, { recursive: true });
let recovered = 0;
sources.forEach((source, i) => {
    const content = contents[i];
    if (content == null) {
        console.log(`  skipped (no content): ${source}`);
        return;
    }
    const safe = source.replace(/^[./\\]+/, "").replace(/\.\.\//g, "").replace(/[:*?"<>|]/g, "_");
    const outPath = path.join(outDir, safe);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, content);
    recovered += 1;
});
console.log(`recovered ${recovered} original source file(s) into ${outDir}`);
