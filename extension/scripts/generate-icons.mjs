/**
 * Regenerate extension toolbar icons from icons/source.png (macOS sips).
 * Source may be JPEG despite a .png extension — always convert to PNG first.
 */
import { execFileSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, unlinkSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const extRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const iconsDir = join(extRoot, "icons");
const source = join(iconsDir, "source.png");
const legacySource = join(extRoot, "src", "sayane_icon.png");
const pngWork = join(iconsDir, ".source-rgba.png");

mkdirSync(iconsDir, { recursive: true });

if (!existsSync(source)) {
  if (!existsSync(legacySource)) {
    console.error("Missing icons/source.png (or legacy src/sayane_icon.png)");
    process.exit(1);
  }
  copyFileSync(legacySource, source);
}

try {
  execFileSync("sips", ["-s", "format", "png", source, "--out", pngWork], {
    stdio: "pipe",
  });
  copyFileSync(pngWork, source);
} finally {
  if (existsSync(pngWork)) unlinkSync(pngWork);
}

const sizes = [16, 32, 48, 128];
for (const size of sizes) {
  const out = join(iconsDir, `icon${size}.png`);
  execFileSync("sips", ["-z", String(size), String(size), source, "--out", out], {
    stdio: "inherit",
  });
}

console.log(
  `Generated ${sizes.map((s) => `icons/icon${s}.png`).join(", ")} (PNG)`,
);
