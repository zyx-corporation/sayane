import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  canApproveCandidate,
  canQuickApprove,
  effectiveCandidateStatus,
  getApproveAvailability,
  syncSummaryFromDetail,
} from "./approve-availability.js";
import type { CandidateDetail } from "./types.js";
import type { CandidateSummary } from "./types.js";

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

describe("getApproveAvailability", () => {
  it("pending approve is disabled on collapsed and expanded cards", () => {
    const c = summary({ status: "pending" });
    const expanded = getApproveAvailability(c, undefined, { compact: false });
    assert.equal(expanded.kind, "needs_evaluation");
    assert.equal(expanded.enabled, false);
    assert.equal(expanded.labelKey, "candidate.approve");
    assert.equal(expanded.reasonKey, "review.approve_requires_evaluation");

    const collapsed = getApproveAvailability(c, undefined, { compact: true });
    assert.equal(collapsed.kind, "needs_evaluation");
    assert.equal(collapsed.enabled, false);
    assert.equal(canQuickApprove(c), false);
  });

  it("canQuickApprove requires evaluated status", () => {
    const pending = summary({ status: "pending", section: "knowledge.concepts" });
    assert.equal(canQuickApprove(pending), false);

    const evaluated = summary({
      status: "evaluated",
      section: "knowledge.concepts",
      rde_class: "Authorized Transformation",
    });
    assert.equal(canQuickApprove(evaluated), true);
  });

  it("evaluated important_terms disabled without explicit confirmation", () => {
    const c = summary({
      status: "evaluated",
      rde_class: "Authorized Transformation",
    });
    const avail = getApproveAvailability(c);
    assert.equal(avail.kind, "needs_explicit_confirmation");
    assert.equal(avail.enabled, false);
    assert.equal(avail.reasonKey, "review.approve_explicit_check_and_reason");
    assert.equal(canQuickApprove(c), false);
    assert.equal(canApproveCandidate(c), false);
  });

  it("evaluated important_terms enabled with check and reason", () => {
    const c = summary({
      status: "evaluated",
      rde_class: "Authorized Transformation",
    });
    const avail = getApproveAvailability(c, undefined, {
      explicitConfirmation: { checked: true, reason: "差分を確認済み。" },
    });
    assert.equal(avail.kind, "can_approve");
    assert.equal(avail.enabled, true);
    assert.equal(
      canApproveCandidate(c, undefined, {
        explicitConfirmation: { checked: true, reason: "差分を確認済み。" },
      }),
      true,
    );
  });

  it("explicit confirmation disabled with check but empty reason", () => {
    const c = summary({
      status: "evaluated",
      rde_class: "Authorized Transformation",
    });
    const avail = getApproveAvailability(c, undefined, {
      explicitConfirmation: { checked: true, reason: "" },
    });
    assert.equal(avail.enabled, false);
    assert.equal(avail.reasonKey, "review.approve_explicit_reason_required");
  });

  it("explicit confirmation disabled with reason but no check", () => {
    const c = summary({
      status: "evaluated",
      rde_class: "Authorized Transformation",
    });
    const avail = getApproveAvailability(c, undefined, {
      explicitConfirmation: { checked: false, reason: "理由あり" },
    });
    assert.equal(avail.enabled, false);
    assert.equal(avail.reasonKey, "review.approve_explicit_check_required");
  });

  it("merge unsupported section stays blocked after UI refresh", () => {
    const c = summary({
      status: "evaluated",
      section: "persona",
      rde_class: "Authorized Transformation",
    });
    const avail = getApproveAvailability(c);
    assert.equal(avail.kind, "blocked");
    assert.equal(avail.enabled, false);
  });

  it("pending never allows compact quick approve", () => {
    const c = summary({ status: "pending", section: "knowledge.concepts" });
    assert.equal(canQuickApprove(c), false);
  });

  it("critical distortion on important_terms needs override after explicit confirm", () => {
    const c = summary({
      status: "evaluated",
      section: "important_terms",
      rde_class: "Critical Distortion",
    });
    const explicitOnly = getApproveAvailability(c, undefined, {
      explicitConfirmation: { checked: true, reason: "ok" },
    });
    assert.equal(explicitOnly.kind, "requires_override");
    assert.equal(explicitOnly.enabled, false);

    const full = getApproveAvailability(c, undefined, {
      explicitConfirmation: { checked: true, reason: "ok" },
      overrideConfirmation: {
        required: true,
        checked: true,
        reason: "override ok",
      },
    });
    assert.equal(full.kind, "can_approve");
    assert.equal(full.enabled, true);
    assert.equal(canQuickApprove(c), false);
  });

  it("values.core evaluated safe requires override confirmation before enable", () => {
    const c = summary({
      status: "evaluated",
      section: "values.core",
      rde_class: "Authorized Transformation",
    });
    const blocked = getApproveAvailability(c);
    assert.equal(blocked.kind, "requires_override");
    assert.equal(blocked.enabled, false);
    assert.equal(canQuickApprove(c), false);

    const ready = getApproveAvailability(c, undefined, {
      overrideConfirmation: {
        required: true,
        checked: true,
        reason: "understood",
      },
    });
    assert.equal(ready.kind, "can_approve");
    assert.equal(ready.enabled, true);
  });

  it("effective status prefers detail over stale summary", () => {
    const c = summary({ status: "pending" });
    const detail = {
      id: c.id,
      status: "evaluated",
      proposal: { section: "important_terms" },
      evaluation: { rde_class: "Authorized Transformation", level: 1 },
    } as CandidateDetail;
    assert.equal(effectiveCandidateStatus(c, detail), "evaluated");
    syncSummaryFromDetail(c, detail);
    assert.equal(c.status, "evaluated");
    assert.equal(c.rde_class, "Authorized Transformation");
  });

  it("approving card action state disables approve", () => {
    const c = summary({
      status: "evaluated",
      section: "knowledge.concepts",
      rde_class: "Authorized Transformation",
    });
    const avail = getApproveAvailability(c, undefined, {
      cardActionState: "approving",
    });
    assert.equal(avail.enabled, false);
    assert.equal(avail.labelKey, "busy.approving");
  });
});
