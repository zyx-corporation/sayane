import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import {
  captureExcerptForReview,
  captureExcerptFromDetail,
  candidateInReviewSession,
  detectCaptureScopeMismatch,
  detectImportantTermsLargeCapture,
  filterProposalItemsForSection,
  filterStoredContextForSection,
} from "./capture-excerpt.js";
import { classifyCandidate, isPersonaDump } from "./candidate-review-class.js";
import type { CandidateDetail, CandidateSummary } from "./types.js";

function detail(partial: Partial<CandidateDetail> & Pick<CandidateDetail, "id">): CandidateDetail {
  return {
    status: "pending",
    target_profile_id: "default",
    source: "clipboard",
    source_url: null,
    captured_at: new Date().toISOString(),
    rde_class: null,
    evaluation_level: null,
    section: "important_terms",
    content_preview: "important_terms:",
    content: "persona:\n  preferred_name: stale",
    source_excerpt: "important_terms:\n  - \"RDE\"",
    raw_capture: "important_terms:\n  - \"RDE\"",
    proposal: { section: "important_terms", add: [], summary: null },
    evaluation: null,
    ...partial,
  };
}

function summary(partial: Partial<CandidateSummary> & Pick<CandidateSummary, "id">): CandidateSummary {
  return {
    status: "pending",
    target_profile_id: "default",
    source: "clipboard",
    source_url: null,
    captured_at: new Date().toISOString(),
    rde_class: null,
    evaluation_level: null,
    section: "important_terms",
    content_preview: "important_terms:",
    ...partial,
  };
}

test("captureExcerptForReview uses session rawCaptureText for session candidates", () => {
  const fragment = "important_terms:\n  - \"RDE\"\n  - \"Sayane\"";
  const excerpt = captureExcerptForReview(
    detail({
      id: "new-cap",
      content: "persona:\n  preferred_name: old",
      raw_capture: "persona:\n  preferred_name: old",
    }),
    {
      captureId: "new-cap",
      candidateIds: ["new-cap"],
      rawCaptureText: fragment,
    },
  );
  assert.ok(excerpt.includes("important_terms"));
  assert.ok(!excerpt.includes("preferred_name"));
});

test("captureExcerptFromDetail never uses content field", () => {
  const excerpt = captureExcerptFromDetail(
    detail({
      id: "x",
      source_excerpt: undefined,
      raw_capture: null,
      cleaned_capture: null,
      display_summary: null,
      content: "persona:\n  preferred_name: must-not-appear",
    }),
  );
  assert.equal(excerpt, "");
});

test("captureExcerptFromDetail prefers source_excerpt from bridge", () => {
  const excerpt = captureExcerptFromDetail(detail({ id: "a" }));
  assert.ok(excerpt.includes("important_terms"));
  assert.ok(!excerpt.includes("preferred_name"));
});

test("partial important_terms yaml is not a persona dump", () => {
  const text = "important_terms:\n  - \"制度詩学\"";
  assert.equal(isPersonaDump(text, "important_terms"), false);
  const c = summary({ id: "t", section: "important_terms", content_preview: text });
  assert.equal(classifyCandidate(c), "new_candidate");
});

test("detectImportantTermsLargeCapture flags long clipboard lists", () => {
  const six = "important_terms:\n  - \"a\"\n  - \"b\"\n  - \"c\"\n  - \"d\"\n  - \"e\"\n  - \"f\"\n";
  assert.equal(detectImportantTermsLargeCapture(six), false);
  const many = `${six}  - \"g\"\n  - \"h\"\n  - \"i\"\n`;
  assert.equal(detectImportantTermsLargeCapture(many), true);
});

test("filterStoredContextForSection hides persona paths for important_terms", () => {
  const filtered = filterStoredContextForSection(
    [
      { path: "identity.preferred_name", name: "tomyuk" },
      { path: "core_concepts[].name", name: "RDE" },
    ],
    "important_terms",
  );
  assert.equal(filtered.length, 1);
  assert.equal((filtered[0] as { name: string }).name, "RDE");
});

test("candidateInReviewSession matches captureId or candidateIds", () => {
  assert.equal(
    candidateInReviewSession("abc", {
      captureId: "abc",
      candidateIds: ["abc"],
      rawCaptureText: "x",
    }),
    true,
  );
  assert.equal(
    candidateInReviewSession("abc", {
      captureId: "other",
      candidateIds: ["abc"],
      rawCaptureText: "x",
    }),
    true,
  );
});

test("captureExcerptForReview falls back when session rawCaptureText is empty", () => {
  const excerpt = captureExcerptForReview(
    detail({ id: "new-cap" }),
    {
      captureId: "new-cap",
      candidateIds: ["new-cap"],
      rawCaptureText: "",
    },
  );
  assert.ok(excerpt.includes("important_terms"));
});

test("detectCaptureScopeMismatch flags short excerpt with many persona proposals", () => {
  const d = detail({
    id: "m",
    proposal: {
      section: "persona",
      add: [],
      summary: "Persona YAML: 222 new field(s)",
      items: Array.from({ length: 222 }, (_, i) => ({
        yaml_path: `persona.field_${i}`,
        name: `value_${i}`,
      })),
    },
  });
  const excerpt = "important_terms:\n  - \"RDE\"";
  assert.equal(detectCaptureScopeMismatch(d, excerpt), true);
});

test("filterProposalItemsForSection keeps only important_terms for that section", () => {
  const d = detail({
    id: "f",
    proposal: {
      section: "important_terms",
      add: [],
      summary: null,
      items: [
        { yaml_path: "important_terms[0]", name: "RDE" },
        { yaml_path: "persona.email", name: "secret@example.com" },
      ],
    },
  });
  const filtered = filterProposalItemsForSection(d);
  assert.equal(filtered.length, 1);
  assert.equal(filtered[0].yaml_path, "important_terms[0]");
});

test("sidepanel uses captureExcerptForReview with session", () => {
  const src = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "sidepanel-candidate-ui.ts"),
    "utf8",
  );
  assert.ok(src.includes("captureExcerptForReview(detail, currentReviewSession)"));
  assert.ok(src.includes("listDiffFromBridgeDiff"));
  assert.ok(!src.includes("detail.content.slice(0, 1200)"));
});
