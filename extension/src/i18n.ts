/** Extension UI localization (en / ja). */

import { loadConfig } from "./config.js";
import type { DisplayLanguage, SupportedLocale } from "./types.js";

export type { DisplayLanguage, SupportedLocale } from "./types.js";

const catalogCache = new Map<SupportedLocale, Record<string, string>>();

let activeLocale: SupportedLocale = "en";

export function normalizeLocale(code: string): SupportedLocale {
  const base = code.trim().replace("_", "-").split("-")[0].toLowerCase();
  return base === "ja" ? "ja" : "en";
}

async function loadCatalog(locale: SupportedLocale): Promise<Record<string, string>> {
  const cached = catalogCache.get(locale);
  if (cached) return cached;
  const res = await fetch(chrome.runtime.getURL(`locale/${locale}.json`));
  if (!res.ok) throw new Error(`Locale catalog missing: ${locale}`);
  const parsed = (await res.json()) as Record<string, string>;
  catalogCache.set(locale, parsed);
  return parsed;
}

export async function resolveDisplayLocale(language: DisplayLanguage): Promise<SupportedLocale> {
  if (language === "en" || language === "ja") return language;
  return normalizeLocale(navigator.language || "en");
}

export async function initI18n(): Promise<SupportedLocale> {
  const config = await loadConfig();
  activeLocale = await resolveDisplayLocale(config.displayLanguage);
  await loadCatalog("en");
  await loadCatalog(activeLocale);
  document.documentElement.lang = activeLocale;
  return activeLocale;
}

export function getLocale(): SupportedLocale {
  return activeLocale;
}

export function t(key: string, params?: Record<string, string | number>): string {
  const primary = catalogCache.get(activeLocale)?.[key];
  const fallback = catalogCache.get("en")?.[key];
  let template = primary ?? fallback ?? key;
  if (params) {
    for (const [name, value] of Object.entries(params)) {
      template = template.replaceAll(`{${name}}`, String(value));
    }
  }
  return template;
}

export function applyDataI18n(root: ParentNode = document): void {
  root.querySelectorAll<HTMLElement>("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (key) el.textContent = t(key);
  });
  root.querySelectorAll<HTMLElement>("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    if (key && "placeholder" in el) {
      (el as HTMLInputElement).placeholder = t(key);
    }
  });
  root.querySelectorAll<HTMLElement>("[data-i18n-title]").forEach((el) => {
    const key = el.dataset.i18nTitle;
    if (key) el.title = t(key);
  });
}

/** Map known English API / Bridge errors to locale keys. */
export function localizeError(message: string): string {
  const known: Record<string, string> = {
    "Bridge token not configured. Set it in Options.": "error.bridge_token",
    "No text selected": "status.no_text_selected",
    "Could not read page": "status.could_not_read_page",
    "No active tab": "error.no_active_tab",
    "Cannot capture on this page. Open a normal https:// page (e.g. https://example.com), select text, reload the tab if you just updated the extension, then try again.":
      "error.restricted_page",
  };
  const key = known[message];
  return key ? t(key) : message;
}
