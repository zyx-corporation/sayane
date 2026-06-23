import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const extRoot = join(dirname(fileURLToPath(import.meta.url)), "..");

test("popup page detail localizes readable boolean through catalog values", () => {
  const src = readFileSync(join(extRoot, "src", "popup.ts"), "utf8");
  assert.ok(src.includes('t("page.detail.page_readable"'));
  assert.ok(src.includes('? t("page.value.available") : t("page.value.unavailable")'));
});
