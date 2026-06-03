import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  buildRdeSummaryFromDiff,
  captureSourceFromMeta,
  isMixedDiff,
  shouldMentionPageCaptureNoise,
} from "./diff-summary.js";
import type { CandidateDetail } from "./types.js";

function candidate(overrides: Partial<CandidateDetail> = {}): CandidateDetail {
  return {
    id: "c1",
    status: "evaluated",
    target_profile_id: "default",
    source: "selection",
    source_url: null,
    captured_at: "2026-01-01T00:00:00Z",
    rde_class: null,
    evaluation_level: 1,
    content_preview: "",
    content: "x",
    proposal: {
      section: "mixed_sections",
      add: [],
      items: [],
      already_present: [{ path: "core_concepts[].name", name: "RDE" }],
      summary: null,
    },
    evaluation: {
      level: 1,
      rde_class: "Suspicious Drift",
      notes: [],
    },
    ...overrides,
  } as CandidateDetail;
}

describe("captureSourceFromMeta", () => {
  it("prefers explicit capture_source", () => {
    assert.equal(
      captureSourceFromMeta({ capture_source: "selection", user_selected: false }),
      "selection",
    );
  });
});

describe("buildRdeSummaryFromDiff", () => {
  it("does not mention page capture for selection mixed_sections", () => {
    const c = candidate({
      capture_meta: {
        capture_source: "selection",
        user_selected: true,
        capture_warnings: [],
      },
    } as CandidateDetail & { capture_meta: object });
    const msg = buildRdeSummaryFromDiff(
      c,
      {
        section: "mixed_sections",
        recommended_section: "review_required",
        has_duplicates: true,
        profile_update_recommended: false,
      },
      "ja",
    );
    assert.ok(msg.includes("選択範囲"));
    assert.ok(!msg.includes("ページ全体Capture"));
    assert.ok(isMixedDiff({ section: "mixed_sections", recommended_section: "review_required" }, c));
  });

  it("mentions page capture for page source with warnings", () => {
    const c = candidate({
      source: "page",
      capture_meta: {
        capture_source: "page",
        user_selected: false,
        capture_warnings: ["page_capture_low_confidence", "ui_noise_detected"],
        capture_confidence: "low",
      },
    } as CandidateDetail & { capture_meta: object });
    const msg = buildRdeSummaryFromDiff(
      c,
      {
        section: "mixed_sections",
        recommended_section: "review_required",
        has_duplicates: true,
        profile_update_recommended: false,
      },
      "ja",
    );
    assert.ok(msg.includes("ページ全体Capture"));
    assert.ok(shouldMentionPageCaptureNoise(c.capture_meta as never));
  });

  it("user_selected true without page warnings does not use page capture wording", () => {
    const meta = { capture_source: "selection" as const, user_selected: true, capture_warnings: [] };
    assert.equal(shouldMentionPageCaptureNoise(meta), false);
  });
});
