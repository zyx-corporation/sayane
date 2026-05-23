import type { ExtensionConfig } from "./types.js";

export const DEFAULT_BRIDGE_URL = "http://127.0.0.1:38741";

export const STORAGE_KEYS = {
  bridgeUrl: "bridgeUrl",
  bridgeToken: "bridgeToken",
  defaultProfileId: "defaultProfileId",
} as const;

export const DEFAULT_CONFIG: ExtensionConfig = {
  bridgeUrl: DEFAULT_BRIDGE_URL,
  bridgeToken: "",
  defaultProfileId: "default",
};

export async function loadConfig(): Promise<ExtensionConfig> {
  const stored = await chrome.storage.sync.get([
    STORAGE_KEYS.bridgeUrl,
    STORAGE_KEYS.bridgeToken,
    STORAGE_KEYS.defaultProfileId,
  ]);
  return {
    bridgeUrl: (stored[STORAGE_KEYS.bridgeUrl] as string) || DEFAULT_CONFIG.bridgeUrl,
    bridgeToken: (stored[STORAGE_KEYS.bridgeToken] as string) || DEFAULT_CONFIG.bridgeToken,
    defaultProfileId:
      (stored[STORAGE_KEYS.defaultProfileId] as string) || DEFAULT_CONFIG.defaultProfileId,
  };
}

export async function saveConfig(partial: Partial<ExtensionConfig>): Promise<void> {
  await chrome.storage.sync.set(partial);
}
