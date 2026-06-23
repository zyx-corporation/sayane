import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const extRoot = join(dirname(fileURLToPath(import.meta.url)), "..");

test("i18n helper supports aria-label attributes", () => {
  const src = readFileSync(join(extRoot, "src", "i18n.ts"), "utf8");
  assert.ok(src.includes("data-i18n-aria-label"));
  assert.ok(src.includes('setAttribute("aria-label", t(key))'));
});

test("html uses i18n attributes for remaining accessibility labels", () => {
  const sidepanel = readFileSync(join(extRoot, "sidepanel.html"), "utf8");
  const options = readFileSync(join(extRoot, "options.html"), "utf8");
  const diff = readFileSync(join(extRoot, "diff.html"), "utf8");
  assert.ok(sidepanel.includes('data-i18n-aria-label="review.filter.all"'));
  assert.ok(sidepanel.includes('data-i18n-aria-label="candidate.refresh"'));
  assert.ok(sidepanel.includes('data-i18n-title="candidate.refresh"'));
  assert.ok(options.includes('data-i18n-aria-label="options.build_info"'));
  assert.ok(options.includes('data-i18n-placeholder="options.bridge_url_placeholder"'));
  assert.ok(options.includes('data-i18n-placeholder="options.default_profile_placeholder"'));
  assert.ok(diff.includes('data-i18n="diff.title"'));
  assert.ok(diff.includes('data-i18n="candidate.evaluate"'));
  assert.ok(diff.includes('data-i18n="candidate.approve"'));
  assert.ok(diff.includes('data-i18n="candidate.reject"'));
  assert.ok(diff.includes('data-i18n="diff.section.raw"'));
});

test("html fallback text for localized sidepanel filters stays English-neutral", () => {
  const sidepanel = readFileSync(join(extRoot, "sidepanel.html"), "utf8");
  assert.ok(
    sidepanel.includes("Comparison against your saved 紗綾音 context. This is not LLM memory."),
  );
  assert.ok(sidepanel.includes("Review required"));
  assert.ok(sidepanel.includes("All"));
  assert.ok(sidepanel.includes("Reject recommended"));
  assert.ok(sidepanel.includes("Has diff"));
  assert.ok(sidepanel.includes("Inferred extension"));
  assert.ok(sidepanel.includes("Low value"));
});

test("japanese locale copy prefers localized bridge and debug labels", () => {
  const ja = JSON.parse(readFileSync(join(extRoot, "locale", "ja.json"), "utf8")) as Record<string, string>;
  assert.equal(ja["debug.toggle"], "デバッグ");
  assert.equal(ja["review.filter.debug"], "デバッグ");
  assert.equal(ja["debug.failed"], "失敗");
  assert.equal(ja["debug.no_response"], "応答なし");
  assert.ok(ja["options.build.bridge"].includes("ローカルブリッジ"));
  assert.ok(ja["popup.bridge.connected"].includes("ローカルブリッジ"));
  assert.ok(ja["resident_app.meta"].includes("契約"));
  assert.ok(ja["review.capture_excerpt"].includes("取り込み"));
  assert.ok(ja["review.lineage.capture"].includes("取り込み"));
  assert.ok(ja["detail.parent_capture"].includes("取り込み"));
  assert.equal(ja["review.session.source.selection"], "選択範囲");
  assert.equal(ja["review.session.source.clipboard"], "クリップボード");
  assert.equal(ja["review.session.source.page"], "ページ");
  assert.equal(ja["review.session.source.manual"], "手動");
  assert.equal(ja["review.lineage.source_manual"], "手動");
  assert.equal(ja["review.value.pending"], "保留");
  assert.equal(ja["review.value.evaluated"], "評価済み");
  assert.equal(ja["review.value.approved"], "承認済み");
  assert.equal(ja["review.value.rejected"], "却下済み");
  assert.equal(ja["detail.storage_kind.context_note"], "文脈ノート");
  assert.equal(ja["detail.storage_kind.prompt_fragment"], "プロンプト断片");
  assert.equal(ja["review.value.manual"], "手動");
  assert.equal(ja["diff.section.raw"], "元のCapture全文（raw）");
});
