/** Open side panel and notify candidate list refresh. */

const CANDIDATES_TICK_KEY = "sayane.candidatesTick";
const CANDIDATES_FOCUS_KEY = "sayane.candidatesFocusId";

export async function openSidePanel(): Promise<void> {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const windowId = tabs[0]?.windowId;
  if (windowId == null) return;
  await chrome.runtime.sendMessage({ type: "OPEN_SIDE_PANEL", windowId });
}

export async function notifyCandidatesChanged(candidateId?: string): Promise<void> {
  await chrome.storage.local.set({
    [CANDIDATES_TICK_KEY]: Date.now(),
    [CANDIDATES_FOCUS_KEY]: candidateId ?? null,
  });
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
