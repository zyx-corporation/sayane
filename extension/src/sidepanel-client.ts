/** Open side panel and notify candidate list refresh. */

import {
  beginReviewSession,
  CANDIDATES_FOCUS_KEY,
  CANDIDATES_TICK_KEY,
  type BeginReviewSessionParams,
  type ReviewCaptureSource,
} from "./review-session.js";

/** Call synchronously inside a click handler (manual “open review” only). */
export function openSidePanelOnUserGesture(): void {
  void chrome.sidePanel.open({ windowId: chrome.windows.WINDOW_ID_CURRENT });
}

const POPUP_REOPEN_DELAYS_MS = [0, 100, 250] as const;

/** Chrome 118+: restore action popup after sidePanel.open() dismissed it. */
export async function reopenExtensionPopup(windowId: number): Promise<boolean> {
  if (!chrome.action?.openPopup) {
    return false;
  }
  for (const delayMs of POPUP_REOPEN_DELAYS_MS) {
    if (delayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    try {
      await chrome.action.openPopup({ windowId });
      return true;
    } catch {
      /* retry — panel animation may block the first attempt */
    }
  }
  return false;
}

export type AfterCaptureReviewParams = {
  captureId: string;
  source: ReviewCaptureSource;
  profileId: string;
  candidateIds: string[];
  rawCaptureText: string;
};

/**
 * After a successful capture (from background): replace the review session and refresh UI.
 * sidePanel.open() must run from the popup click handler (user gesture), not here.
 */
export async function afterCaptureNotifyReview(
  windowId: number,
  params: AfterCaptureReviewParams,
): Promise<void> {
  await beginReviewSession({
    captureId: params.captureId,
    source: params.source,
    profileId: params.profileId,
    candidateIds: params.candidateIds,
    rawCaptureText: params.rawCaptureText,
  });
  if (await isSidePanelOpenInWindow(windowId)) {
    return;
  }
  await reopenExtensionPopup(windowId);
}

export async function isSidePanelOpenInWindow(windowId: number): Promise<boolean> {
  if (!chrome.runtime.getContexts) {
    return false;
  }
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ["SIDE_PANEL"] as chrome.runtime.ContextType[],
  });
  return contexts.some((ctx: chrome.runtime.ExtensionContext) => ctx.windowId === windowId);
}

export async function openSidePanel(): Promise<void> {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const windowId = tabs[0]?.windowId;
  if (windowId == null) return;
  if (await isSidePanelOpenInWindow(windowId)) {
    return;
  }
  await chrome.runtime.sendMessage({ type: "OPEN_SIDE_PANEL", windowId });
}

export async function notifyCandidatesChanged(candidateId?: string): Promise<void> {
  await chrome.storage.local.set({
    [CANDIDATES_TICK_KEY]: Date.now(),
    [CANDIDATES_FOCUS_KEY]: candidateId ?? null,
  });
}

/** Latest capture id written by beginReviewSession (for panel init race). */
export async function peekCandidatesFocusId(): Promise<string | null> {
  const stored = await chrome.storage.local.get(CANDIDATES_FOCUS_KEY);
  const focus = stored[CANDIDATES_FOCUS_KEY];
  return typeof focus === "string" ? focus : null;
}

export function watchCandidatesChanged(
  onChange: (candidateId: string | null) => void,
): () => void {
  const listener = (
    changes: Record<string, chrome.storage.StorageChange>,
    area: string,
  ) => {
    if (area !== "local" || !changes[CANDIDATES_TICK_KEY]) return;
    void chrome.storage.local.get(CANDIDATES_FOCUS_KEY).then((stored) => {
      const focus = stored[CANDIDATES_FOCUS_KEY];
      onChange(typeof focus === "string" ? focus : null);
    });
  };
  chrome.storage.onChanged.addListener(listener);
  return () => chrome.storage.onChanged.removeListener(listener);
}

export type { BeginReviewSessionParams, ReviewCaptureSource };
