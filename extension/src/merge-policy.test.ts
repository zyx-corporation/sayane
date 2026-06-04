import assert from "node:assert/strict";
import test from "node:test";
import {
  canMergeSection,
  requiresForceCriticalMerge,
} from "./merge-policy.js";

test("voice.tone requires force_critical to merge", () => {
  assert.equal(requiresForceCriticalMerge("voice.tone"), true);
  assert.equal(canMergeSection("voice.tone", false), false);
  assert.equal(canMergeSection("voice.tone", true), true);
});

test("knowledge.concepts merges without force_critical", () => {
  assert.equal(requiresForceCriticalMerge("knowledge.concepts"), false);
  assert.equal(canMergeSection("knowledge.concepts", false), true);
});
