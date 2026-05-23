import type { SiteAdapter } from "./types.js";

export const chatgptAdapter: SiteAdapter = {
  id: "chatgpt",
  matches(url: string): boolean {
    try {
      const host = new URL(url).hostname;
      return host === "chatgpt.com" || host === "chat.openai.com";
    } catch {
      return false;
    }
  },
  inputSelectors: [
    "#prompt-textarea",
    "textarea[data-id]",
    "textarea[placeholder]",
    'div[contenteditable="true"]#prompt-textarea',
    'div[contenteditable="true"]',
  ],
  failureHint:
    "ChatGPT DOM may have changed. Try pasting from clipboard or update site adapter selectors.",
};
