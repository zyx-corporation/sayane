import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { BusyUiController } from "./busy-ui.js";
import {
  canApproveCandidate,
  getApproveAvailability,
  canQuickApprove,
} from "./approve-availability.js";
import { recommendedActionKeyForCandidate } from "./candidate-review-class.js";
import type { CandidateSummary } from "./types.js";

const src = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "sidepanel-candidate-ui.ts"),
  "utf8",
);

function summary(overrides: Partial<CandidateSummary> = {}): CandidateSummary {
  return {
    id: "c1",
    status: "pending",
    captured_at: "2026-06-04T00:00:00Z",
    section: "important_terms",
    content_preview: "important_terms:",
    ...overrides,
  };
}

test("pending candidates do not auto-approve or auto-evaluate from approve click", () => {
  assert.ok(!src.includes("ensureEvaluatedForApprove"));
  assert.ok(src.includes("runApproveEvaluated"));
  assert.ok(src.includes("handleApproveClick"));
  const needsEvalBlock = src.match(
    /if \(avail\.kind === "needs_evaluation"\) \{[\s\S]*?\n    \}/,
  );
  assert.ok(needsEvalBlock);
  assert.ok(!needsEvalBlock![0].includes("runEvaluate"));
  assert.ok(needsEvalBlock![0].includes("review.approve_requires_evaluation"));
});

test("applyCardActionUi uses getApproveAvailability for approve buttons", () => {
  assert.ok(src.includes("approveOptionsFor"));
  assert.ok(src.includes("canApproveCandidate"));
  assert.ok(src.includes("readApproveContextFromActions"));
  assert.ok(src.includes("readApproveContextFromButton"));
  assert.ok(src.includes("bindApproveInputsRefresh"));
  assert.ok(src.includes("bindApproveInputRefresh"));
  assert.ok(src.includes("expandedActionsForApproveButton"));
  assert.ok(src.includes("expandedApproveSync.get(candidateId)"));
  assert.ok(src.includes("approveUnavailableMessage"));
  assert.ok(src.includes("approve-blocked-hint"));
  assert.ok(!src.includes("canInitiateApproveFromDetail"));
  assert.ok(!src.includes("ensureEvaluatedForApprove"));
});

test("evaluated important_terms not approvable without explicit confirmation state", () => {
  const c = summary({
    status: "evaluated",
    rde_class: "Authorized Transformation",
  });
  assert.equal(canApproveCandidate(c), false);
  assert.equal(
    canApproveCandidate(c, undefined, {
      explicitConfirmation: { checked: true, reason: "確認済み" },
    }),
    true,
  );
});

test("pending expanded recommends evaluate, not approve", () => {
  const c = summary({ status: "pending" });
  assert.equal(recommendedActionKeyForCandidate(c), "review.action.evaluate_before_approve");
  assert.equal(canQuickApprove(c), false);
  const avail = getApproveAvailability(c, undefined, { compact: false });
  assert.equal(avail.enabled, false);
  assert.equal(avail.labelKey, "candidate.approve");
});

test("blocked and unsupported sections stay approve-disabled", () => {
  const persona = summary({
    status: "evaluated",
    section: "persona",
    rde_class: "Authorized Transformation",
  });
  assert.equal(getApproveAvailability(persona).enabled, false);

  const blocked = getApproveAvailability(
    summary({
      status: "evaluated",
      section: "identity.name",
      rde_class: "Authorized Transformation",
    }),
  );
  assert.equal(blocked.enabled, false);
});

test("approveOptionsFor reads explicit confirmation from actions element", () => {
  assert.ok(
    src.includes(
      "!compact && actionsEl\n        ? readApproveContextFromActions(actionsEl)",
    ),
  );
});

test("override panel wires input refresh for expanded approve button", () => {
  assert.ok(src.includes(".override-reason"));
  assert.ok(src.includes(".override-check"));
  assert.ok(src.includes("bindApproveInputsRefresh(actions, syncExpandedApprove)"));
  assert.ok(src.includes("syncExpandedApprove()"));
  assert.ok(src.includes("btnRow.appendChild(approveBtn)"));
  assert.ok(src.includes("actions.appendChild(btnRow)"));
  const bindIdx = src.indexOf("bindApproveInputsRefresh(actions, syncExpandedApprove)");
  const bodyAppendIdx = src.indexOf("body.appendChild(actions)");
  assert.ok(bindIdx > 0 && bodyAppendIdx > 0 && bindIdx > bodyAppendIdx);
  const bindBlock = src.match(
    /function bindApproveInputsRefresh[\s\S]*?function refreshExpandedApproveUi/,
  );
  assert.ok(bindBlock);
  assert.ok(bindBlock![0].includes(".override-reason"));
  assert.ok(bindBlock![0].includes(".override-check"));
});

test("persona dump blocks compact quick approve", () => {
  const c = summary({
    status: "evaluated",
    section: "mixed_sections",
    content_preview: "persona:\n  name: test\n".repeat(200),
    rde_class: "Authorized Transformation",
  });
  assert.equal(canQuickApprove(c), false);
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
