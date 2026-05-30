import { matchesLocalCustom } from "./local-host.js";
import type { ProviderAdapter } from "./types.js";

export const localCustomProvider: ProviderAdapter = {
  id: "local-custom",
  target: "local-custom",
  profileKey: "local",
  kind: "local",
  labelKey: "insert.local_custom",
  bridgeContextPacketSupported: false,
  origins: ["http://127.0.0.1/*", "http://localhost/*"],
  matches(url: string): boolean {
    return matchesLocalCustom(url);
  },
  inputSelectors: [
    "textarea",
    'div[contenteditable="true"]',
    "input[type='text']",
  ],
  failureHint:
    "Local UI input not found. Open your custom local LLM page with a visible text field.",
};
