import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { isBusyActionState } from "./candidate-action-state.js";

test("isBusyActionState is true while approving", () => {
  assert.equal(isBusyActionState("approving"), true);
  assert.equal(isBusyActionState("idle"), false);
  assert.equal(isBusyActionState("approved"), false);
});

test("sidepanel uses per-candidate cardActions and applyCardActionUi", () => {
  const src = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "sidepanel-candidate-ui.ts"),
    "utf8",
  );
  assert.ok(src.includes("cardActions"));
  assert.ok(src.includes("applyCardActionUi"));
  assert.ok(src.includes('setCardAction(candidateId, "approving")'));
  assert.ok(src.includes("busy.approving"));
});
