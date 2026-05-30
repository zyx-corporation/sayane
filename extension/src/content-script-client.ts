/** Page interactions via chrome.scripting (MV3-safe). */

import { getProviderById } from "./providers/registry.js";
import type { ContentResponse, InsertTarget } from "./types.js";

const CONTENT_SCRIPT_FILE = "dist/content.js";

export function isRestrictedTabUrl(url: string | undefined): boolean {
  if (!url) return true;
  try {
    const { protocol } = new URL(url);
    return (
      protocol === "chrome:" ||
      protocol === "chrome-extension:" ||
      protocol === "edge:" ||
      protocol === "about:" ||
      protocol === "moz-extension:"
    );
  } catch {
    return true;
  }
}

export const RESTRICTED_PAGE_HINT =
  "Cannot capture on this page. Open a normal https:// page (e.g. https://example.com), select text, reload the tab if you just updated the extension, then try again.";

type InPageInsertResult = {
  ok: boolean;
  error?: string;
  code?: string;
};

/** In-page insert logic (must stay in sync with sites/registry.ts setElementText). */
function inPageInsert(insertText: string, selectors: string[]): InPageInsertResult {
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (!(el instanceof HTMLElement)) continue;
    if (el instanceof HTMLTextAreaElement || el instanceof HTMLInputElement) {
      el.value = insertText;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.focus();
      return { ok: true };
    }
    if (el.isContentEditable) {
      el.textContent = insertText;
      el.dispatchEvent(new InputEvent("input", { bubbles: true }));
      el.focus();
      return { ok: true };
    }
  }
  return { ok: false, code: "INPUT_NOT_FOUND", error: "Could not find input" };
}

/** Insert context text on ChatGPT / Claude (host_permissions + activeTab). */
export async function insertTextInTab(
  tabId: number,
  text: string,
  target: InsertTarget,
): Promise<ContentResponse> {
  const tab = await chrome.tabs.get(tabId);
  const url = tab.url ?? "";
  if (isRestrictedTabUrl(url)) {
    return { ok: false, error: RESTRICTED_PAGE_HINT, code: "UNSUPPORTED_SITE" };
  }

  const adapter = getProviderById(target);
  if (!adapter) {
    return {
      ok: false,
      code: "UNSUPPORTED_SITE",
      error: "No provider adapter for this target",
    };
  }
  if (!adapter.matches(url)) {
    return {
      ok: false,
      code: "SITE_MISMATCH",
      error: `Page does not match adapter ${adapter.id}`,
      hint: adapter.failureHint,
    };
  }

  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    args: [text, [...adapter.inputSelectors]],
    func: inPageInsert,
  });

  const inserted = (result?.result ?? { ok: false, error: "Insert failed" }) as InPageInsertResult;
  if (inserted.ok) {
    return { ok: true, inserted: true };
  }
  return {
    ok: false,
    error: inserted.error ?? "Insert failed",
    code: inserted.code,
    hint: adapter.failureHint,
  };
}

/** Read selection via scripting API (activeTab + host_permissions). */
export async function readSelectionFromTab(tabId: number): Promise<string> {
  const tab = await chrome.tabs.get(tabId);
  if (isRestrictedTabUrl(tab.url)) {
    throw new Error(RESTRICTED_PAGE_HINT);
  }
  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => window.getSelection()?.toString().trim() ?? "",
  });
  return (result?.result as string) ?? "";
}

/** Read page snapshot via scripting API (logic mirrors content.ts getPageSnapshot). */
export async function readPageFromTab(tabId: number): Promise<string> {
  const tab = await chrome.tabs.get(tabId);
  if (isRestrictedTabUrl(tab.url)) {
    throw new Error(RESTRICTED_PAGE_HINT);
  }
  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => {
      const title = document.title || "Untitled";
      const url = location.href;
      const body = document.body?.innerText?.trim() ?? "";
      const maxLen = 8000;
      const excerpt =
        body.length > maxLen ? `${body.slice(0, maxLen)}\n...[truncated]` : body;
      return `Title: ${title}\nURL: ${url}\n\n${excerpt}`;
    },
  });
  return (result?.result as string) ?? "";
}
