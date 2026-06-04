import assert from "node:assert/strict";
import test from "node:test";
import { formatSourceUpdatedAt } from "./build-info-display.js";
import { EXTENSION_BUILD_INFO } from "./build-info.js";

test("formatSourceUpdatedAt returns dash for empty input", () => {
  assert.equal(formatSourceUpdatedAt(""), "—");
});

test("formatSourceUpdatedAt formats ISO timestamp", () => {
  const formatted = formatSourceUpdatedAt("2026-06-02T10:15:30+09:00");
  assert.ok(formatted.includes("2026"));
});

test("EXTENSION_BUILD_INFO has version and sourceUpdatedAt", () => {
  assert.match(EXTENSION_BUILD_INFO.version, /^\d+\.\d+/);
  assert.match(EXTENSION_BUILD_INFO.sourceUpdatedAt, /^\d{4}-\d{2}-\d{2}T/);
  assert.notEqual(EXTENSION_BUILD_INFO.sourceUpdatedAt, "1970-01-01T00:00:00.000Z");
});
