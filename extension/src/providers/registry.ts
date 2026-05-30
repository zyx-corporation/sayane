import { chatgptProvider } from "./chatgpt.js";
import { claudeProvider } from "./claude.js";
import { deepseekProvider } from "./deepseek.js";
import { geminiProvider } from "./gemini.js";
import { localCustomProvider } from "./local-custom.js";
import { localOpenwebuiProvider } from "./local-openwebui.js";
import type { InsertResult, InsertTarget, ProviderAdapter } from "./types.js";

const providers: ProviderAdapter[] = [
  chatgptProvider,
  claudeProvider,
  geminiProvider,
  deepseekProvider,
  localOpenwebuiProvider,
  localCustomProvider,
];

/** Bridge compile targets supported by Core (`sayane.adapters.factory`). */
export const BRIDGE_CONTEXT_PACKET_TARGETS = new Set<InsertTarget>(["chatgpt", "claude", "gemini"]);

export function listProviders(): readonly ProviderAdapter[] {
  return providers;
}

/** Active Insert buttons (Bridge context-packet available). */
export function listPopupInsertProviders(): readonly ProviderAdapter[] {
  return providers.filter((p) => p.bridgeContextPacketSupported);
}

/** Registered DOM adapters awaiting Bridge compile (#85 / future). */
export function listPreviewInsertProviders(): readonly ProviderAdapter[] {
  return providers.filter((p) => !p.bridgeContextPacketSupported);
}

/** @deprecated Use listPopupInsertProviders or listProviders. */
export function listInsertProviders(): readonly ProviderAdapter[] {
  return listPopupInsertProviders();
}

export function getProviderForUrl(url: string): ProviderAdapter | null {
  return providers.find((p) => p.matches(url)) ?? null;
}

export function getProviderById(id: string): ProviderAdapter | null {
  return providers.find((p) => p.id === id) ?? null;
}

export function hostPermissions(): string[] {
  const seen = new Set<string>();
  for (const provider of providers) {
    for (const origin of provider.origins) {
      seen.add(origin);
    }
  }
  seen.add("http://127.0.0.1/*");
  seen.add("http://localhost/*");
  return [...seen];
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

export function insertTextIntoPage(url: string, text: string, targetId: InsertTarget | string): InsertResult {
  const adapter = getProviderById(targetId) ?? getProviderForUrl(url);
  if (!adapter) {
    return {
      ok: false,
      code: "UNSUPPORTED_SITE",
      error: "No provider adapter for this page",
      hint: "Open a supported LLM UI or use clipboard copy.",
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
