import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  analyzeClipboardText,
  countImportantTermsInCapture,
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
});
