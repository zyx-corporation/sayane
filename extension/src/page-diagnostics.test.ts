import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { deriveCaptureAvailability } from "./page-diagnostics.js";
import type { SayanePingResult } from "./capture/page-extract-core.js";

const t = (key: string, params?: Record<string, string | number>): string => {
  if (params) {
    return `${key}:${JSON.stringify(params)}`;
  }
  return key;
};

function ping(overrides: Partial<SayanePingResult> = {}): SayanePingResult {
  return {
    ok: true,
    provider: "chatgpt",
    url: "https://chatgpt.com/c/abc",
    title: "Chat",
    readable: true,
    selectionTextLength: 0,
    extractorAvailable: true,
    extractorError: null,
    hostPermissionOk: true,
    contentScriptReady: true,
    ...overrides,
  };
}

describe("deriveCaptureAvailability", () => {
  it("keeps bridge connected when page extractor fails", () => {
    const avail = deriveCaptureAvailability(
      { kind: "connected" },
      { kind: "extractor_failed", ping: ping({ readable: false, extractorAvailable: false }), reason: "fail" },
      1,
      "https://chatgpt.com/c/abc",
      t,
    );
    assert.equal(avail.bridgeState.kind, "connected");
    assert.equal(avail.canCapturePage, false);
  });

  it("enables selection capture when extractor fails but selection exists", () => {
    const avail = deriveCaptureAvailability(
      { kind: "connected" },
      {
        kind: "extractor_failed",
        ping: ping({ readable: false, extractorAvailable: false, selectionTextLength: 42 }),
        reason: "fail",
      },
      1,
      "https://chatgpt.com/c/abc",
      t,
    );
    assert.equal(avail.canCaptureSelection, true);
    assert.equal(avail.canCapturePage, false);
  });

  it("disables both captures when bridge is down", () => {
    const avail = deriveCaptureAvailability(
      { kind: "failed", reason: "down" },
      { kind: "readable", ping: ping({ selectionTextLength: 10 }) },
      1,
      "https://chatgpt.com/",
      t,
    );
    assert.equal(avail.canCaptureSelection, false);
    assert.equal(avail.canCaptureClipboard, false);
    assert.equal(avail.canCapturePage, false);
  });

  it("requires selection length for selection capture", () => {
    const avail = deriveCaptureAvailability(
      { kind: "connected" },
      { kind: "readable", ping: ping({ selectionTextLength: 0 }) },
      1,
      "https://chatgpt.com/",
      t,
    );
    assert.equal(avail.canCaptureSelection, false);
    assert.equal(avail.canCapturePage, true);
  });

  it("enables selection capture when ping uses cached selection length", () => {
    const avail = deriveCaptureAvailability(
      { kind: "connected" },
      {
        kind: "readable",
        ping: ping({
          selectionTextLength: 24,
          selectionCurrentLength: 0,
          selectionCachedLength: 24,
          selectionCacheAgeMs: 1200,
        }),
      },
      1,
      "https://chatgpt.com/",
      t,
    );
    assert.equal(avail.canCaptureSelection, true);
    assert.ok(
      avail.debugLines.some((line) => line.includes("debug.selection_cached_length")),
    );
  });
});
