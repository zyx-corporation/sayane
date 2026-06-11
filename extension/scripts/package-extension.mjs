/**
 * Package the built extension into a release zip for GitHub Releases.
 *
 * Produces:
 *   release/sayane-extension-v{version}.zip
 *   release/sayane-extension-v{version}.zip.sha256
 *
 * The zip root contains manifest.json, so Chrome can load it as an
 * unpacked extension directly after extraction.
 *
 * Usage: node scripts/package-extension.mjs
 *   (run from extension/ directory; requires `npm run build` first)
 */

import { createHash } from "node:crypto";
import { execSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { join } from "node:path";

const rootDir = process.cwd();
const distDir = join(rootDir, "dist");
const releaseDir = join(rootDir, "release");

// Read version from manifest.json (authoritative for Chrome)
const manifest = JSON.parse(
  readFileSync(join(rootDir, "manifest.json"), "utf-8"),
);
const version = manifest.version;

if (!version || typeof version !== "string") {
  console.error("Could not read version from manifest.json");
  process.exit(1);
}

if (!existsSync(distDir)) {
  console.error("dist/ not found. Run `npm run build` first.");
  process.exit(1);
}

if (!existsSync(join(rootDir, "manifest.json"))) {
  console.error("manifest.json not found.");
  process.exit(1);
}

// ---------- stage files ----------

const zipBase = `sayane-extension-v${version}`;
const stageDir = join(releaseDir, zipBase);

// Clean and recreate staging directory
if (existsSync(stageDir)) rmSync(stageDir, { recursive: true });
mkdirSync(stageDir, { recursive: true });

// Copy static assets (manifest.json, HTML files)
cpSync(join(rootDir, "manifest.json"), join(stageDir, "manifest.json"));
for (const name of readdirSync(rootDir)) {
  if (/\.html$/.test(name)) {
    cpSync(join(rootDir, name), join(stageDir, name));
  }
}

// Copy icons
if (existsSync(join(rootDir, "icons"))) {
  cpSync(join(rootDir, "icons"), join(stageDir, "icons"), {
    recursive: true,
  });
}

// Copy locale
if (existsSync(join(rootDir, "locale"))) {
  cpSync(join(rootDir, "locale"), join(stageDir, "locale"), {
    recursive: true,
  });
}

// Copy compiled dist
cpSync(distDir, join(stageDir, "dist"), { recursive: true });

// ---------- create zip ----------

const zipName = `${zipBase}.zip`;
const zipPath = join(releaseDir, zipName);

// Remove old zip if present
if (existsSync(zipPath)) rmSync(zipPath);

try {
  execSync(`cd "${stageDir}" && zip -r "${zipPath}" .`, {
    stdio: "pipe",
  });
} catch (err) {
  console.error("Failed to create zip. Is `zip` installed?");
  console.error(err.stderr?.toString() ?? err.message);
  process.exit(1);
}

// ---------- verify manifest.json at zip root ----------

let manifestAtRoot = false;
try {
  const list = execSync(`unzip -l "${zipPath}"`, { encoding: "utf-8" });
  manifestAtRoot = /^\s+\d+\s+[\d-]+\s+[\d:]+\s+manifest\.json$/m.test(list);
} catch {
  // unzip not available — skip verification
}

// ---------- generate SHA256 checksum ----------

const zipData = readFileSync(zipPath);
const sha256 = createHash("sha256").update(zipData).digest("hex");
const checksumPath = `${zipPath}.sha256`;
writeFileSync(checksumPath, `${sha256}  ${zipName}\n`, "utf-8");

// ---------- clean up staging ----------

rmSync(stageDir, { recursive: true });

// ---------- summary ----------

const zipSizeKb = (statSync(zipPath).size / 1024).toFixed(1);

console.log("");
console.log("Release package created:");
console.log(`  ${zipPath}  (${zipSizeKb} KB)`);
console.log(`  ${checksumPath}`);
console.log(`  SHA256: ${sha256}`);
if (!manifestAtRoot) {
  console.warn("  Warning: could not verify manifest.json at zip root.");
}
console.log("");
console.log("Installation:");
console.log("  1. Extract the zip");
console.log(`     unzip ${zipName} -d ${zipBase}`);
console.log("  2. Open chrome://extensions/");
console.log("  3. Enable Developer mode");
console.log(`  4. Load unpacked → select the ${zipBase}/ directory`);
