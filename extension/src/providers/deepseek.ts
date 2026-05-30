import type { ProviderAdapter } from "./types.js";

export const deepseekProvider: ProviderAdapter = {
  id: "deepseek",
  target: "deepseek",
  profileKey: "deepseek",
  kind: "hosted",
  labelKey: "insert.deepseek",
  bridgeContextPacketSupported: false,
  origins: ["https://chat.deepseek.com/*"],
  matches(url: string): boolean {
    try {
      return new URL(url).hostname === "chat.deepseek.com";
    } catch {
      return false;
    }
  },
  inputSelectors: [
    "textarea",
    'div[contenteditable="true"]',
    'textarea[placeholder]',
  ],
  failureHint:
    "DeepSeek DOM may have changed. Try pasting from clipboard or update provider adapter selectors.",
};
