import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  analyzeClipboardText,
  buildLargeImportantTermsConfirmMessage,
  countImportantTermsInCapture,
  parseImportantTermsInCapture,
  shouldConfirmLargeImportantTermsCapture,
} from "./clipboard-preview.js";

const SIX_TERMS = `important_terms:
  - "柏崎刈羽原子力発電所"
  - "制度詩学"
  - "RDE"
  - "RDE vNext"
  - "T-RDE"
  - "ΔM"
`;

describe("clipboard preview", () => {
  it("counts six important_terms entries", () => {
    assert.equal(countImportantTermsInCapture(SIX_TERMS), 6);
    const preview = analyzeClipboardText(SIX_TERMS);
    assert.equal(preview.importantTermsCount, 6);
    assert.equal(shouldConfirmLargeImportantTermsCapture(preview), false);
  });

  it("requires confirm when more than eight terms", () => {
    const many = `${SIX_TERMS}  - "制度的シコファンシー"
  - "Kotone"
  - "Kotonoha"
  - "Sayane"
`;
    const preview = analyzeClipboardText(many);
    assert.ok(preview.importantTermsCount > 8);
    assert.equal(shouldConfirmLargeImportantTermsCapture(preview), true);
  });

  it("parseImportantTermsInCapture returns quoted list values", () => {
    const terms = parseImportantTermsInCapture(SIX_TERMS);
    assert.equal(terms.length, 6);
    assert.deepEqual(terms[0], "柏崎刈羽原子力発電所");
    assert.equal(countImportantTermsInCapture(SIX_TERMS), terms.length);
  });

  it("parse twelve terms for preflight scenario (9 existing + 3 new labels)", () => {
    const existing = Array.from({ length: 9 }, (_, i) => `term-${String(i + 1).padStart(2, "0")}`);
    const clipboard = [
      ...existing,
      "new-alpha",
      "new-beta",
      "new-gamma",
    ];
    const text = `important_terms:\n${clipboard.map((t) => `  - "${t}"`).join("\n")}\n`;
    assert.equal(parseImportantTermsInCapture(text).length, 12);
  });

  it("preflight confirm message uses total/existing/added", () => {
    const msg = buildLargeImportantTermsConfirmMessage(
      { charCount: 1, lineCount: 1, importantTermsCount: 12, hasImportantTermsSection: true },
      { section: "important_terms", total: 12, existing_count: 9, added_count: 3, removed_count: 0 },
      (key, params) => `${key}:${params?.total}/${params?.existing}/${params?.added}`,
    );
    assert.match(msg, /12\/9\/3/);
  });

  it("falls back to raw count message when preflight unavailable", () => {
    const msg = buildLargeImportantTermsConfirmMessage(
      { charCount: 1, lineCount: 1, importantTermsCount: 12, hasImportantTermsSection: true },
      null,
      (key, params) => `${key}:${params?.count ?? ""}`,
    );
    assert.match(msg, /clipboard_confirm_many:12/);
  });
});
