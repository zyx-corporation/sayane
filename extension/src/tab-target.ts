/** Resolve the browser tab that Capture / diagnostics should target. */

import { isRestrictedTabUrl } from "./content-script-client.js";

const EXTENSION_PAGE_RE = /^chrome-extension:\/\//;

export function isExtensionPageUrl(url: string | undefined): boolean {
  if (!url) return true;
  return EXTENSION_PAGE_RE.test(url) || isRestrictedTabUrl(url);
}

/** Tab suitable for content-script ping and capture (not Options / chrome://). */
export async function getActiveCaptureTab(): Promise<chrome.tabs.Tab | null> {
  const [tab] = await chrome.tabs.query({
    active: true,
    currentWindow: true,
    lastFocusedWindow: true,
  });
  if (!tab?.id) return null;
  if (isExtensionPageUrl(tab.url)) return null;
  return tab;
}
