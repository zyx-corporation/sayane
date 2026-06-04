import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  getSelectionCacheSnapshot,
  getSelectionText,
  readCurrentSelectionText,
  refreshSelectionCache,
  resetSelectionCacheForTests,
  SELECTION_CACHE_TTL_MS,
} from "./selection-cache.js";

type MockSelection = {
  text: string;
  collapsed: boolean;
};

let mockSelection: MockSelection = { text: "", collapsed: true };

function installSelectionMock(): void {
  const selection = () =>
    ({
      toString: () => mockSelection.text,
      get isCollapsed() {
        return mockSelection.collapsed;
      },
    }) as Selection;
  globalThis.window = {
    getSelection: selection,
    addEventListener: () => {},
  } as unknown as Window & typeof globalThis;
  globalThis.document = {
    addEventListener: () => {},
  } as unknown as Document;
}

describe("selection cache", { concurrency: 1 }, () => {
  it("readCurrentSelectionText returns trimmed non-collapsed selection", () => {
  installSelectionMock();
  resetSelectionCacheForTests();
  mockSelection = { text: "  hello  ", collapsed: false };
  assert.equal(readCurrentSelectionText(), "hello");
  mockSelection = { text: "x", collapsed: true };
  assert.equal(readCurrentSelectionText(), "");
});

  it("getSelectionText returns cached text when live selection is empty", () => {
  installSelectionMock();
  resetSelectionCacheForTests();
  const now = 1_000_000;
  mockSelection = { text: "cached phrase", collapsed: false };
  assert.equal(getSelectionText(now), "cached phrase");
  mockSelection = { text: "", collapsed: true };
  assert.equal(getSelectionText(now + 1_000), "cached phrase");
  assert.equal(getSelectionText(now + SELECTION_CACHE_TTL_MS), "cached phrase");
});

  it("getSelectionText does not return expired cache", () => {
  installSelectionMock();
  resetSelectionCacheForTests();
  const now = 2_000_000;
  mockSelection = { text: "old", collapsed: false };
  assert.equal(getSelectionText(now), "old");
  mockSelection = { text: "", collapsed: true };
  assert.equal(getSelectionText(now + SELECTION_CACHE_TTL_MS + 1), "");
  });

  it("getSelectionText prefers live selection over cache", () => {
  installSelectionMock();
  resetSelectionCacheForTests();
  mockSelection = { text: "old", collapsed: false };
  refreshSelectionCache();
  mockSelection = { text: "new", collapsed: false };
  assert.equal(getSelectionText(), "new");
});

  it("getSelectionCacheSnapshot reports current vs cached lengths", () => {
  installSelectionMock();
  resetSelectionCacheForTests();
  const now = 3_000_000;
  mockSelection = { text: "abcdef", collapsed: false };
  assert.equal(getSelectionText(now), "abcdef");
  mockSelection = { text: "", collapsed: true };
  const snap = getSelectionCacheSnapshot(now + 500);
  assert.equal(snap.currentLength, 0);
  assert.equal(snap.cachedLength, 6);
  assert.equal(snap.cacheAgeMs, 500);
  });
});
