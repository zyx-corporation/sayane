import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";
import { deriveCaptureAvailability } from "./page-diagnostics.js";

const extRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const t = (key: string): string => key;

describe("capture input design", () => {
  it("clipboard confirm wording does not imply raw count equals new additions (Fixes #126)", () => {
    const ja = JSON.parse(
      readFileSync(join(extRoot, "locale/ja.json"), "utf8"),
    ) as Record<string, string>;
    const en = JSON.parse(
      readFileSync(join(extRoot, "locale/en.json"), "utf8"),
    ) as Record<string, string>;
    assert.ok(ja["capture.clipboard_confirm_many"].includes("Capture 後に確認"));
    assert.ok(en["capture.clipboard_confirm_many"].includes("checked after Capture"));
    assert.ok(!ja["capture.clipboard_confirm_many"].includes("6 行だけ"));
  });

  it("manifest includes clipboardRead permission", () => {
    const manifest = JSON.parse(
      readFileSync(join(extRoot, "manifest.json"), "utf8"),
    ) as { permissions?: string[] };
    assert.ok(manifest.permissions?.includes("clipboardRead"));
  });

  it("popup hides page capture in developer panel by default", () => {
    const html = readFileSync(join(extRoot, "popup.html"), "utf8");
    assert.ok(html.includes('id="btn-capture-clipboard"'));
    assert.ok(html.includes('id="developer-capture-panel"'));
    assert.match(html, /developer-capture-panel[^>]*hidden/);
    assert.ok(!html.includes('id="btn-capture-page"') || html.indexOf("developer-capture-panel") < html.indexOf("btn-capture-page"));
  });

  it("popup hides bridge check and page recheck until debug UI is enabled", () => {
    const html = readFileSync(join(extRoot, "popup.html"), "utf8");
    assert.ok(html.includes('id="input-debug-actions"'));
    assert.match(html, /input-debug-actions[^>]*hidden/);
    assert.ok(html.includes('id="btn-bridge-check"'));
    assert.ok(html.includes('id="btn-recheck-page"'));
  });

  it("clipboard capture available when bridge is connected without page ping", () => {
    const avail = deriveCaptureAvailability(
      { kind: "connected" },
      { kind: "no_active_tab", reason: "no tab" },
      null,
      null,
      t,
    );
    assert.equal(avail.canCaptureClipboard, true);
    assert.equal(avail.canCaptureSelection, false);
  });
});
