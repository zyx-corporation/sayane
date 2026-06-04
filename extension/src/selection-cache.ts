/**
 * Retain the last non-empty page selection when popup/side panel clears getSelection().
 */

export const SELECTION_CACHE_TTL_MS = 30_000;

let lastSelectionText = "";
let lastSelectionAt = 0;

export function readCurrentSelectionText(): string {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) return "";
  return selection.toString().trim();
}

export function refreshSelectionCache(): void {
  const text = readCurrentSelectionText();
  if (!text) return;
  lastSelectionText = text;
  lastSelectionAt = Date.now();
}

export function getSelectionText(now: number = Date.now()): string {
  const current = readCurrentSelectionText();
  if (current) {
    lastSelectionText = current;
    lastSelectionAt = now;
    return current;
  }

  if (lastSelectionText && now - lastSelectionAt <= SELECTION_CACHE_TTL_MS) {
    return lastSelectionText;
  }

  return "";
}

export type SelectionCacheSnapshot = {
  currentLength: number;
  cachedLength: number;
  cacheAgeMs: number | null;
};

export function getSelectionCacheSnapshot(now: number = Date.now()): SelectionCacheSnapshot {
  const current = readCurrentSelectionText();
  const cacheAgeMs =
    lastSelectionText && lastSelectionAt > 0 ? Math.max(0, now - lastSelectionAt) : null;
  return {
    currentLength: current.length,
    cachedLength: lastSelectionText.length,
    cacheAgeMs,
  };
}

export function registerSelectionCacheListeners(): void {
  document.addEventListener("selectionchange", refreshSelectionCache);
  window.addEventListener("mouseup", refreshSelectionCache);
  window.addEventListener("keyup", refreshSelectionCache);
  window.addEventListener("pointerup", refreshSelectionCache);
  window.addEventListener("touchend", refreshSelectionCache);
}

/** Test-only reset of module cache state. */
export function resetSelectionCacheForTests(): void {
  lastSelectionText = "";
  lastSelectionAt = 0;
}
