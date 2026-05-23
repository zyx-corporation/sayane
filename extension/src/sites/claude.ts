import type { SiteAdapter } from "./types.js";

export const claudeAdapter: SiteAdapter = {
  id: "claude",
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
    "Claude DOM may have changed. Try pasting from clipboard or update site adapter selectors.",
};
