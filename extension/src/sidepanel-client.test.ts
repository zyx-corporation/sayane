import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const extRoot = join(dirname(fileURLToPath(import.meta.url)), "..");

test("capture opens side panel on user gesture before async work", () => {
  const src = readFileSync(join(extRoot, "src", "popup.ts"), "utf8");
  const clipboardHandler = src.slice(
    src.indexOf('$("btn-capture-clipboard").addEventListener'),
    src.indexOf('$("btn-bridge-check").addEventListener'),
  );
  assert.match(clipboardHandler, /openSidePanelOnUserGesture\(\)/);
  const gestureIdx = clipboardHandler.indexOf("openSidePanelOnUserGesture()");
  const busyIdx = clipboardHandler.indexOf('busyUi.run("capturingClipboard"');
  assert.ok(gestureIdx >= 0 && busyIdx >= 0 && gestureIdx < busyIdx);
});

test("background does not call sidePanel.open after capture", () => {
  const src = readFileSync(join(extRoot, "src", "sidepanel-client.ts"), "utf8");
  assert.ok(src.includes("afterCaptureNotifyReview"));
  assert.ok(!src.includes("afterCaptureOpenReview"));
  const notifyFn = src.slice(
    src.indexOf("export async function afterCaptureNotifyReview"),
    src.indexOf("export async function isSidePanelOpenInWindow"),
  );
  assert.ok(!notifyFn.includes("sidePanel.open"));
});

test("setCaptureStatus does not notify or open side panel from popup", () => {
  const src = readFileSync(join(extRoot, "src", "popup.ts"), "utf8");
  const fn = src.slice(
    src.indexOf("function setCaptureStatus"),
    src.indexOf("async function insertContext"),
  );
  assert.ok(!fn.includes("notifyCandidatesChanged"));
  assert.ok(!fn.includes("openSidePanel"));
});

test("peekCandidatesFocusId reads storage focus key", () => {
  const src = readFileSync(join(extRoot, "src", "sidepanel-client.ts"), "utf8");
  assert.ok(src.includes("peekCandidatesFocusId"));
});

test("afterCaptureNotifyReview replaces review session via beginReviewSession", () => {
  const src = readFileSync(join(extRoot, "src", "sidepanel-client.ts"), "utf8");
  const fn = src.slice(
    src.indexOf("export async function afterCaptureNotifyReview"),
    src.indexOf("export async function isSidePanelOpenInWindow"),
  );
  assert.ok(fn.includes("beginReviewSession"));
  assert.ok(fn.includes("candidateIds"));
});

test("renderCards clears expanded ids when focusing new capture", () => {
  const src = readFileSync(join(extRoot, "src", "sidepanel-candidate-ui.ts"), "utf8");
  assert.ok(src.includes("expandedCandidateIds.clear()"));
  assert.ok(src.includes("loadGeneration"));
});
