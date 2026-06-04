import assert from "node:assert/strict";
import test from "node:test";
import {
  diffStringList,
  importantTermsCardSummary,
  listDiffFromProposal,
} from "./list-diff.js";
import type { CandidateDetail, CandidateSummary } from "./types.js";

const EXISTING = [
  "柏崎刈羽原子力発電所",
  "制度詩学",
  "RDE",
  "RDE vNext",
  "T-RDE",
  "ΔM",
  "制度的シコファンシー",
  "Kotone",
  "Kotonoha",
  "Sayane",
  "Awai Commons",
];

test("important_terms diff only shows added items", () => {
  const proposed = [...EXISTING, "Context-Aware Harness", "ZAI統合アーキテクチャ"];
  const diff = diffStringList(EXISTING, proposed);
  assert.deepEqual(diff.added, ["Context-Aware Harness", "ZAI統合アーキテクチャ"]);
  assert.deepEqual(diff.removed, []);
  assert.equal(diff.unchanged.length, 11);
});

test("important_terms candidate summary describes added item count", () => {
  const c: CandidateSummary = {
    id: "x",
    status: "pending",
    target_profile_id: "default",
    source: "clipboard",
    source_url: null,
    captured_at: new Date().toISOString(),
    rde_class: null,
    evaluation_level: null,
    section: "important_terms",
    content_preview:
      "important_terms に 2 件の追加候補があります。追加: Context-Aware Harness, ZAI統合アーキテクチャ",
    display_summary:
      "important_terms に 2 件の追加候補があります。追加: Context-Aware Harness, ZAI統合アーキテクチャ",
  };
  const summary = importantTermsCardSummary(c);
  assert.ok(summary?.includes("2 件の追加候補"));
  assert.ok(summary?.includes("Context-Aware Harness"));
  assert.ok(summary?.includes("ZAI統合アーキテクチャ"));
  assert.ok(!summary?.includes("柏崎刈羽原子力発電所"));
});

test("listDiffFromProposal uses items and already_present", () => {
  const detail = {
    id: "d",
    status: "pending",
    target_profile_id: "default",
    source: "clipboard",
    source_url: null,
    captured_at: new Date().toISOString(),
    rde_class: null,
    evaluation_level: null,
    section: "important_terms",
    content_preview: "",
    content: "",
    proposal: {
      section: "important_terms",
      add: [],
      summary: null,
      items: [
        { name: "Context-Aware Harness", yaml_path: "important_terms[]" },
        { name: "ZAI統合アーキテクチャ", yaml_path: "important_terms[]" },
      ],
      already_present: EXISTING.map((name) => ({ name, path: "important_terms[]" })),
    },
    evaluation: null,
  } as CandidateDetail;
  const diff = listDiffFromProposal(detail);
  assert.equal(diff?.added.length, 2);
  assert.equal(diff?.unchanged.length, 11);
});
