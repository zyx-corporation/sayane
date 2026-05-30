import type { ProviderAdapter } from "./types.js";

const OPENWEBUI_HOSTS = new Set(["localhost", "127.0.0.1"]);

export const localOpenwebuiProvider: ProviderAdapter = {
  id: "local-openwebui",
  target: "local-openwebui",
  profileKey: "local",
  kind: "local",
  labelKey: "insert.local_openwebui",
  bridgeContextPacketSupported: false,
  origins: ["http://127.0.0.1/*", "http://localhost/*"],
  matches(url: string): boolean {
    try {
      const parsed = new URL(url);
      if (!OPENWEBUI_HOSTS.has(parsed.hostname)) return false;
      return parsed.pathname === "/" || parsed.pathname.startsWith("/chat");
    } catch {
      return false;
    }
  },
  inputSelectors: [
    "#chat-input",
    'textarea[placeholder*="message" i]',
    'textarea[placeholder*="Message" i]',
    "textarea",
    'div[contenteditable="true"]',
  ],
  failureHint:
    "Open WebUI input not found. Ensure the chat page is open and selectors match your Open WebUI version.",
};
