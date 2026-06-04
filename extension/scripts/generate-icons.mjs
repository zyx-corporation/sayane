/**
 * Regenerate extension toolbar icons from icons/source.png (macOS sips).
 */
import { execFileSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const extRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const iconsDir = join(extRoot, "icons");
const source = join(iconsDir, "source.png");
const legacySource = join(extRoot, "src", "sayane_icon.png");

mkdirSync(iconsDir, { recursive: true });

if (!existsSync(source)) {
  if (!existsSync(legacySource)) {
    console.error("Missing icons/source.png (or legacy src/sayane_icon.png)");
    process.exit(1);
  }
  copyFileSync(legacySource, source);
}

for (const size of [16, 48, 128]) {
  const out = join(iconsDir, `icon${size}.png`);
  execFileSync("sips", ["-z", String(size), String(size), source, "--out", out], {
    stdio: "inherit",
  });
}

console.log("Generated icons/icon16.png, icon48.png, icon128.png");
