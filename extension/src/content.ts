/**
 * Content script — capture selection/page and insert context (site adapters).
 */

import { insertTextIntoPage } from "./providers/registry.js";
import type { ContentMessage, ContentResponse } from "./types.js";

const LOADED_KEY = "__sayaneContentScript";

function getSelectionText(): string {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) return "";
  return selection.toString().trim();
}

function getPageSnapshot(): string {
  const title = document.title || "Untitled";
  const url = location.href;
  const body = document.body?.innerText?.trim() ?? "";
  const maxLen = 8000;
  const excerpt = body.length > maxLen ? `${body.slice(0, maxLen)}\n...[truncated]` : body;
  return `Title: ${title}\nURL: ${url}\n\n${excerpt}`;
}

function registerMessageListener(): void {
  const scope = globalThis as typeof globalThis & { [LOADED_KEY]?: boolean };
  if (scope[LOADED_KEY]) return;
  scope[LOADED_KEY] = true;

  chrome.runtime.onMessage.addListener(
    (message: ContentMessage, _sender, sendResponse: (r: ContentResponse) => void) => {
      if (message.type === "GET_SELECTION") {
        sendResponse({ ok: true, text: getSelectionText() });
        return false;
      }
      if (message.type === "GET_PAGE_SNAPSHOT") {
        sendResponse({ ok: true, text: getPageSnapshot() });
        return false;
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
        return false;
      }
      return false;
    },
  );
}

registerMessageListener();
