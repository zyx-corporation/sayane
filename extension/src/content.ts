/**
 * Content script — ping diagnostics, capture, insert (SPA-aware).
 * Built as dist/content.bundle.js (single IIFE, no runtime imports).
 */

import { buildSayanePing, extractPageFromDocument } from "./capture/page-extract-core.js";
import { insertTextIntoPage } from "./providers/registry.js";
import {
  getSelectionCacheSnapshot,
  getSelectionText,
  registerSelectionCacheListeners,
} from "./selection-cache.js";
import type { ContentMessage, ContentResponse } from "./types.js";

console.debug("[Sayane] content script loaded", location.href);

const LISTENER_KEY = "__sayaneMessageListenerRegistered";

function getPageSnapshot(): string {
  const extracted = extractPageFromDocument();
  return extracted.cleaned || extracted.raw;
}

function registerMessageListener(): void {
  const scope = globalThis as typeof globalThis & { [LISTENER_KEY]?: boolean };
  if (scope[LISTENER_KEY]) return;
  scope[LISTENER_KEY] = true;

  chrome.runtime.onMessage.addListener(
    (message: ContentMessage, _sender, sendResponse: (r: ContentResponse) => void) => {
      if (message?.type === "SAYANE_PING") {
        const snap = getSelectionCacheSnapshot();
        sendResponse({
          ...buildSayanePing(),
          selectionTextLength: getSelectionText().length,
          selectionCurrentLength: snap.currentLength,
          selectionCachedLength: snap.cachedLength,
          selectionCacheAgeMs: snap.cacheAgeMs,
        });
        return true;
      }
      if (message.type === "EXTRACT_PAGE") {
        sendResponse(extractPageFromDocument());
        return true;
      }
      if (message.type === "GET_SELECTION") {
        sendResponse({ ok: true, text: getSelectionText() });
        return true;
      }
      if (message.type === "GET_PAGE_SNAPSHOT") {
        sendResponse({ ok: true, text: getPageSnapshot() });
        return true;
      }
      if (message.type === "INSERT_TEXT") {
        const result = insertTextIntoPage(location.href, message.text, message.target);
        if (result.ok) {
          sendResponse({ ok: true, inserted: true });
        } else {
          sendResponse({
            ok: false,
            error: result.error ?? "Insert failed",
            code: result.code,
            hint: result.hint,
          });
        }
        return true;
      }
      return false;
    },
  );
}

function watchSpaNavigation(): void {
  let lastHref = location.href;

  const onHrefMaybeChanged = (): void => {
    if (location.href !== lastHref) {
      lastHref = location.href;
    }
  };

  window.addEventListener("popstate", onHrefMaybeChanged);

  const wrapHistory = <T extends History["pushState"]>(method: T): T => {
    return function (this: History, ...args: Parameters<T>) {
      const result = method.apply(this, args);
      onHrefMaybeChanged();
      return result;
    } as T;
  };

  history.pushState = wrapHistory(history.pushState);
  history.replaceState = wrapHistory(history.replaceState);

  let debounce: ReturnType<typeof setTimeout> | undefined;
  const observer = new MutationObserver(() => {
    clearTimeout(debounce);
    debounce = setTimeout(onHrefMaybeChanged, 400);
  });

  const startObserve = (): void => {
    if (!document.body) return;
    observer.observe(document.body, { childList: true, subtree: true });
  };

  if (document.body) startObserve();
  else document.addEventListener("DOMContentLoaded", startObserve, { once: true });
}

registerSelectionCacheListeners();
registerMessageListener();
watchSpaNavigation();
