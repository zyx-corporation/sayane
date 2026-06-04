import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyCandidate,
  isPersonaDump,
  matchesReviewFilter,
  REVIEW_REQUIRED_CLASSES,
  shouldBlockBulkApprove,
} from "./candidate-review-class.js";
import type { CandidateSummary } from "./types.js";

function summary(partial: Partial<CandidateSummary> & Pick<CandidateSummary, "id">): CandidateSummary {
  return {
    status: "pending",
    target_profile_id: "default",
    source: "test",
    source_url: null,
    captured_at: new Date().toISOString(),
    rde_class: null,
    evaluation_level: null,
    section: "knowledge.concepts",
    content_preview: "sample",
    ...partial,
  };
}

test("review_required filter hides low_value candidates", () => {
  const low = summary({
    id: "a",
    status: "approved",
    rde_class: "Inferred Extension",
  });
  assert.equal(classifyCandidate(low), "low_value");
  assert.equal(matchesReviewFilter(low, "review_required"), false);
  assert.equal(matchesReviewFilter(low, "all"), true);
});

test("critical distortion maps to reject_recommended", () => {
  const c = summary({
    id: "b",
    status: "evaluated",
    rde_class: "Critical Distortion",
  });
  assert.equal(classifyCandidate(c), "reject_recommended");
  assert.ok(REVIEW_REQUIRED_CLASSES.includes("reject_recommended"));
  assert.equal(matchesReviewFilter(c, "review_required"), true);
});

test("persona dump detected as sensitive_review", () => {
  const text = "persona:\ncommunication_mode: formal\n".repeat(80);
  assert.ok(isPersonaDump(text, "knowledge.concepts"));
  const c = summary({ id: "c", content_preview: text });
  assert.equal(classifyCandidate(c), "sensitive_review");
});

test("persona dump blocks bulk approve", () => {
  const text = "persona:\ncommunication_mode: formal\n".repeat(80);
  const c = summary({ id: "e", content_preview: text });
  assert.equal(shouldBlockBulkApprove(c), true);
});

test("inferred extension appears in inferred filter", () => {
  const c = summary({
    id: "d",
    status: "evaluated",
    rde_class: "Inferred Extension",
  });
  assert.equal(matchesReviewFilter(c, "inferred_extension"), true);
});
