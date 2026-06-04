import assert from "node:assert/strict";
import test from "node:test";
import {
  canApproveWithCriticalOverride,
  isKnownRdeCategory,
  rdeCssClass,
  rdeSeverity,
} from "./candidate-display.js";

test("rdeCssClass uses whitelist only", () => {
  assert.equal(rdeCssClass("Critical Distortion"), "rde-critical");
  assert.equal(rdeCssClass("Totally Unknown"), "rde-unknown");
  assert.equal(rdeCssClass(null), "rde-unknown");
});

test("rdeSeverity orders critical highest among known classes", () => {
  assert.ok(rdeSeverity("Critical Distortion") > rdeSeverity("Inferred Extension"));
  assert.equal(rdeSeverity("unknown"), -1);
});

test("isKnownRdeCategory rejects arbitrary strings", () => {
  assert.equal(isKnownRdeCategory("Critical Distortion"), true);
  assert.equal(isKnownRdeCategory("<script>"), false);
});

test("canApproveWithCriticalOverride allows evaluated critical for override flow", () => {
  assert.equal(
    canApproveWithCriticalOverride("evaluated", "Critical Distortion"),
    true,
  );
  assert.equal(
    canApproveWithCriticalOverride("evaluated", "Suspicious Drift"),
    false,
  );
});

test("canApproveWithCriticalOverride allows evaluated when category is missing", () => {
  assert.equal(canApproveWithCriticalOverride("evaluated", null), true);
  assert.equal(canApproveWithCriticalOverride("pending", null), false);
});
