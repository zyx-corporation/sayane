import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { BusyUiController } from "./busy-ui.js";

/**
 * Regression: cards rendered while approving=true bake disabled into DOM buttons
 * that are not wired to BusyUiController.syncDom().
 */
test("approve can run evaluation first when candidate is still pending", () => {
  const src = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "sidepanel-candidate-ui.ts"),
    "utf8",
  );
  assert.ok(src.includes("ensureEvaluatedForApprove"));
  assert.ok(src.includes("canInitiateApprove"));
  assert.ok(src.includes("canQuickApprove"));
  const initiateFn = src.slice(
    src.indexOf("function canInitiateApprove"),
    src.indexOf("function canInitiateApproveFromDetail"),
  );
  assert.ok(!initiateFn.includes("shouldBlockBulkApprove"));
  assert.ok(src.includes('c.status === "pending") return true'));
});

test("candidate buttons should not be created while mutation busy flags are set", async () => {
  const root = { setAttribute() {}, removeAttribute() {} } as unknown as HTMLElement;
  const doc = {
    body: { classList: { add() {}, remove() {} } },
  } as unknown as Document;
  const busyUi = new BusyUiController(root, doc);

  const disabledDuringApprove: boolean[] = [];
  await busyUi.run("approving", async () => {
    disabledDuringApprove.push(busyUi.shouldDisableCandidateActions());
  });
  const disabledAfterApprove: boolean[] = [];
  disabledAfterApprove.push(busyUi.shouldDisableCandidateActions());

  assert.equal(disabledDuringApprove[0], true);
  assert.equal(disabledAfterApprove[0], false);
});
