import type { ProviderAdapter } from "./types.js";

export const claudeProvider: ProviderAdapter = {
  id: "claude",
  target: "claude",
  profileKey: "claude",
  kind: "hosted",
  labelKey: "insert.claude",
  bridgeContextPacketSupported: true,
  origins: ["https://claude.ai/*"],
  matches(url: string): boolean {
    try {
      return new URL(url).hostname === "claude.ai";
    } catch {
      return false;
    }
  },
  inputSelectors: [
    'div[contenteditable="true"].ProseMirror',
    'div[contenteditable="true"]',
    "fieldset textarea",
    "textarea",
  ],
  failureHint:
    "Claude DOM may have changed. Try pasting from clipboard or update provider adapter selectors.",
};
