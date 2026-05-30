import type { ProviderAdapter } from "./types.js";

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1"]);

export const localCustomProvider: ProviderAdapter = {
  id: "local-custom",
  target: "local-custom",
  profileKey: "local",
  kind: "local",
  labelKey: "insert.local_custom",
  bridgeContextPacketSupported: false,
  origins: ["http://127.0.0.1/*", "http://localhost/*"],
  matches(url: string): boolean {
    try {
      const parsed = new URL(url);
      if (!LOCAL_HOSTS.has(parsed.hostname)) return false;
      // Fallback for localhost pages that are not Open WebUI chat UI.
      const path = parsed.pathname;
      return path !== "/" && !path.startsWith("/chat");
    } catch {
      return false;
    }
  },
  inputSelectors: [
    "textarea",
    'div[contenteditable="true"]',
    "input[type='text']",
  ],
  failureHint:
    "Local UI input not found. Open your custom local LLM page with a visible text field.",
};
