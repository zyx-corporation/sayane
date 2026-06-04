import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import {
  classifyCandidate,
  matchesReviewFilter,
} from "./candidate-review-class.js";
import {
  filterCandidatesForReviewSession,
  parseReviewSession,
  type CandidateReviewSession,
} from "./review-session.js";
import type { CandidateSummary } from "./types.js";

const extRoot = join(dirname(fileURLToPath(import.meta.url)), "..");

function summary(
  partial: Partial<CandidateSummary> & Pick<CandidateSummary, "id" | "content_preview">,
): CandidateSummary {
  return {
    status: "pending",
    target_profile_id: "default",
    source: "clipboard",
    source_url: null,
    captured_at: new Date().toISOString(),
    rde_class: null,
    evaluation_level: null,
    section: "knowledge.concepts",
    ...partial,
  };
}

function session(
  candidateIds: string[],
  partial?: Partial<CandidateReviewSession>,
): CandidateReviewSession {
  return {
    captureId: candidateIds[0] ?? "cap",
    source: "clipboard",
    capturedAt: "2026-06-04T12:00:00Z",
    profileId: "default",
    candidateIds,
    rawCaptureText: "",
    ...partial,
  };
}

test("parseReviewSession accepts a valid session with rawCaptureText", () => {
  const parsed = parseReviewSession({
    captureId: "abc",
    source: "page",
    capturedAt: "2026-06-04T12:00:00Z",
    profileId: "default",
    candidateIds: ["abc"],
    rawCaptureText: "important_terms:\n  - RDE",
  });
  assert.deepEqual(parsed, {
    captureId: "abc",
    source: "page",
    capturedAt: "2026-06-04T12:00:00Z",
    profileId: "default",
    candidateIds: ["abc"],
    rawCaptureText: "important_terms:\n  - RDE",
  });
});

test("parseReviewSession rejects invalid payloads", () => {
  assert.equal(parseReviewSession(null), null);
  assert.equal(parseReviewSession({ captureId: "x" }), null);
});

test("filterCandidatesForReviewSession keeps only current session ids", () => {
  const current = session(["new"]);
  const bridge = [
    summary({ id: "old", content_preview: "old yaml" }),
    summary({ id: "new", content_preview: "new yaml" }),
  ];
  const visible = filterCandidatesForReviewSession(bridge, current);
  assert.equal(visible.length, 1);
  assert.equal(visible[0]?.id, "new");
});

test("filterCandidatesForReviewSession returns all without session (graceful fallback)", () => {
  const bridge = [
    summary({ id: "a", content_preview: "first" }),
    summary({ id: "b", content_preview: "second" }),
  ];
  const visible = filterCandidatesForReviewSession(bridge, null);
  assert.equal(visible.length, 2);
  assert.equal(visible[0]?.id, "a");
  assert.equal(visible[1]?.id, "b");
});

test("sidepanel candidate UI scopes list to current review session", () => {
  const src = readFileSync(join(extRoot, "src", "sidepanel-candidate-ui.ts"), "utf8");
  assert.ok(src.includes("filterCandidatesForReviewSession"));
  assert.ok(src.includes("loadCurrentReviewSession"));
  assert.ok(!src.includes("latestCaptureFocusId"));
});

test("after capture notifies with beginReviewSession", () => {
  const src = readFileSync(join(extRoot, "src", "sidepanel-client.ts"), "utf8");
  assert.ok(src.includes("beginReviewSession"));
});

test("review filters only see candidates from the current session", () => {
  const current = session(["new"]);
  const bridge = [
    summary({ id: "old", content_preview: "old yaml", status: "pending" }),
    summary({ id: "new", content_preview: "new yaml", status: "pending" }),
  ];
  const scoped = filterCandidatesForReviewSession(bridge, current);
  for (const filterId of ["review_required", "all", "has_diff"] as const) {
    const visible = scoped.filter((c) => matchesReviewFilter(c, filterId));
    assert.ok(visible.every((c) => c.content_preview.includes("new")));
    assert.ok(!visible.some((c) => c.content_preview.includes("old yaml")));
  }
  assert.equal(classifyCandidate(scoped[0]!), classifyCandidate(bridge[1]!));
});
