import assert from "node:assert/strict";
import test from "node:test";
import { DEFAULT_CONFIG } from "./config.js";

test("showDebugUi defaults to true for backward-compatible debug visibility", () => {
  assert.equal(DEFAULT_CONFIG.showDebugUi, true);
});
