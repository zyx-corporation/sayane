import { chatgptAdapter } from "./chatgpt.js";
import { claudeAdapter } from "./claude.js";
import type { InsertResult, SiteAdapter } from "./types.js";

const adapters: SiteAdapter[] = [chatgptAdapter, claudeAdapter];

export function getAdapterForUrl(url: string): SiteAdapter | null {
  return adapters.find((a) => a.matches(url)) ?? null;
}

export function getAdapterById(id: string): SiteAdapter | null {
  return adapters.find((a) => a.id === id) ?? null;
}

function findInput(selectors: readonly string[]): HTMLElement | null {
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el instanceof HTMLElement) return el;
  }
  return null;
}

function setElementText(el: HTMLElement, text: string): void {
  if (el instanceof HTMLTextAreaElement || el instanceof HTMLInputElement) {
    el.value = text;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.focus();
    return;
  }
  if (el.isContentEditable) {
    el.textContent = text;
    el.dispatchEvent(new InputEvent("input", { bubbles: true }));
    el.focus();
    return;
  }
  throw new Error("Unsupported input element type");
}

export function insertTextIntoPage(url: string, text: string, targetId: string): InsertResult {
  const adapter = getAdapterById(targetId) ?? getAdapterForUrl(url);
  if (!adapter) {
    return {
      ok: false,
      code: "UNSUPPORTED_SITE",
      error: "No site adapter for this page",
      hint: "Open ChatGPT or Claude, or use clipboard copy.",
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
  const input = findInput(adapter.inputSelectors);
  if (!input) {
    return {
      ok: false,
      code: "INPUT_NOT_FOUND",
      error: `Could not find input on ${adapter.id}`,
      hint: adapter.failureHint,
    };
  }
  try {
    setElementText(input, text);
    return { ok: true };
  } catch (err) {
    return {
      ok: false,
      code: "INSERT_FAILED",
      error: err instanceof Error ? err.message : "Insert failed",
      hint: adapter.failureHint,
    };
  }
}
