import type { ProviderAdapter } from "./types.js";

export const geminiProvider: ProviderAdapter = {
  id: "gemini",
  target: "gemini",
  profileKey: "gemini",
  kind: "hosted",
  labelKey: "insert.gemini",
  bridgeContextPacketSupported: false,
  origins: ["https://gemini.google.com/*"],
  matches(url: string): boolean {
    try {
      return new URL(url).hostname === "gemini.google.com";
    } catch {
      return false;
    }
  },
  inputSelectors: [
    'div[contenteditable="true"]',
    "textarea",
    'rich-textarea div[contenteditable="true"]',
    ".ql-editor",
  ],
  failureHint:
    "Gemini DOM may have changed. Try pasting from clipboard or update provider adapter selectors.",
};
