/** Page interactions via content script messages + scripting fallback. */

import { extractPageInDocument, type InPageCaptureResult } from "./capture/in-page-extract.js";
import type { PageExtractPayload } from "./types.js";
import { getProviderById } from "./providers/registry.js";
import type { ContentMessage, ContentResponse, InsertTarget, SayanePingPayload } from "./types.js";

import { CONTENT_SCRIPT_BUNDLE } from "./content-script-bundle.js";

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

function sendContentMessage(tabId: number, message: ContentMessage): Promise<ContentResponse | null> {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, message, (response) => {
      if (chrome.runtime.lastError) {
        resolve(null);
        return;
      }
      resolve((response as ContentResponse) ?? null);
    });
  });
}

export async function ensureContentScriptInjected(tabId: number): Promise<void> {
  const ping = await sendContentMessage(tabId, { type: "SAYANE_PING" });
  if (ping && "contentScriptReady" in ping) return;
  await chrome.scripting.executeScript({
    target: { tabId },
    files: [CONTENT_SCRIPT_BUNDLE],
  });
}

export async function pingContentScript(tabId: number): Promise<SayanePingPayload | null> {
  await ensureContentScriptInjected(tabId);
  const response = await sendContentMessage(tabId, { type: "SAYANE_PING" });
  if (response && "contentScriptReady" in response) {
    return response;
  }
  return null;
}

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

export async function readSelectionFromTab(tabId: number): Promise<string> {
  const tab = await chrome.tabs.get(tabId);
  if (isRestrictedTabUrl(tab.url)) {
    throw new Error(RESTRICTED_PAGE_HINT);
  }

  await ensureContentScriptInjected(tabId);
  const response = await sendContentMessage(tabId, { type: "GET_SELECTION" });
  if (response && "ok" in response && response.ok === true && "text" in response) {
    return response.text;
  }

  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => window.getSelection()?.toString().trim() ?? "",
  });
  return (result?.result as string) ?? "";
}

export type PageCapturePayload = InPageCaptureResult;

function mapExtractPayload(payload: PageExtractPayload): PageCapturePayload {
  return {
    raw: payload.raw,
    cleaned: payload.cleaned,
    provider: payload.provider,
    extractor: payload.extractor,
    uiNoiseDetected: payload.uiNoiseDetected,
    lowConfidence: payload.lowConfidence,
  };
}

export async function readPageFromTab(tabId: number): Promise<PageCapturePayload> {
  const tab = await chrome.tabs.get(tabId);
  if (isRestrictedTabUrl(tab.url)) {
    throw new Error(RESTRICTED_PAGE_HINT);
  }

  await ensureContentScriptInjected(tabId);
  const response = await sendContentMessage(tabId, { type: "EXTRACT_PAGE" });
  if (response && "cleaned" in response && "raw" in response) {
    return mapExtractPayload(response);
  }

  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    func: extractPageInDocument,
  });
  return (
    (result?.result as PageCapturePayload) ?? {
      raw: "",
      cleaned: "",
      provider: "unknown",
      extractor: "fallback",
      uiNoiseDetected: false,
      lowConfidence: true,
    }
  );
}
