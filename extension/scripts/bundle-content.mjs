/**
 * Bundle content script into one classic script (no ES module imports at runtime).
 */
import * as esbuild from "esbuild";
import { readFileSync, unlinkSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const outfile = join(root, "dist/content.bundle.js");

await esbuild.build({
  entryPoints: [join(root, "src/content.ts")],
  bundle: true,
  format: "iife",
  outfile,
  platform: "browser",
  target: "chrome110",
  sourcemap: true,
  splitting: false,
  logLevel: "info",
});

const bundle = readFileSync(outfile, "utf8");
if (/^\s*import\s/m.test(bundle)) {
  throw new Error(`${outfile} must not contain top-level import statements`);
}
if (/^\s*export\s/m.test(bundle)) {
  throw new Error(`${outfile} must not contain export statements`);
}

for (const legacy of ["dist/content.js", "dist/content.js.map"]) {
  try {
    unlinkSync(join(root, legacy));
  } catch {
    // ignore missing legacy artifacts
  }
}
