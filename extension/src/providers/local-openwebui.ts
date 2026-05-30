import { matchesLocalOpenWebUI } from "./local-host.js";
import type { ProviderAdapter } from "./types.js";

export const localOpenwebuiProvider: ProviderAdapter = {
  id: "local-openwebui",
  target: "local-openwebui",
  profileKey: "local",
  kind: "local",
  labelKey: "insert.local_openwebui",
  bridgeContextPacketSupported: true,
  origins: ["http://127.0.0.1/*", "http://localhost/*"],
  matches(url: string): boolean {
    return matchesLocalOpenWebUI(url);
  },
  inputSelectors: [
    "#chat-input",
    '[id^="chat-input-"]',
    'textarea[placeholder*="message" i]',
    'textarea[placeholder*="Message" i]',
    "textarea",
    'div[contenteditable="true"]',
  ],
  failureHint:
    "Open WebUI tab must be active (e.g. http://localhost:3000/ after login, not /auth). Click the Open WebUI tab, then open Sayane popup and Insert again.",
};
