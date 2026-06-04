import type { DisplayLanguage, ExtensionConfig } from "./types.js";

export const DEFAULT_BRIDGE_URL = "http://127.0.0.1:38741";

export const STORAGE_KEYS = {
  bridgeUrl: "bridgeUrl",
  bridgeToken: "bridgeToken",
  defaultProfileId: "defaultProfileId",
  displayLanguage: "displayLanguage",
  developerMode: "developerMode",
  showDebugUi: "showDebugUi",
} as const;

export const DEFAULT_CONFIG: ExtensionConfig = {
  bridgeUrl: DEFAULT_BRIDGE_URL,
  bridgeToken: "",
  defaultProfileId: "default",
  displayLanguage: "auto",
  developerMode: false,
  showDebugUi: true,
};

export async function loadConfig(): Promise<ExtensionConfig> {
  const stored = await chrome.storage.sync.get([
    STORAGE_KEYS.bridgeUrl,
    STORAGE_KEYS.bridgeToken,
    STORAGE_KEYS.defaultProfileId,
    STORAGE_KEYS.displayLanguage,
    STORAGE_KEYS.developerMode,
    STORAGE_KEYS.showDebugUi,
  ]);
  const lang = stored[STORAGE_KEYS.displayLanguage] as string | undefined;
  const displayLanguage: DisplayLanguage =
    lang === "en" || lang === "ja" || lang === "auto" ? lang : DEFAULT_CONFIG.displayLanguage;
  return {
    bridgeUrl: (stored[STORAGE_KEYS.bridgeUrl] as string) || DEFAULT_CONFIG.bridgeUrl,
    bridgeToken: (stored[STORAGE_KEYS.bridgeToken] as string) || DEFAULT_CONFIG.bridgeToken,
    defaultProfileId:
      (stored[STORAGE_KEYS.defaultProfileId] as string) || DEFAULT_CONFIG.defaultProfileId,
    displayLanguage,
    developerMode: Boolean(stored[STORAGE_KEYS.developerMode]),
    showDebugUi:
      stored[STORAGE_KEYS.showDebugUi] === undefined
        ? DEFAULT_CONFIG.showDebugUi
        : Boolean(stored[STORAGE_KEYS.showDebugUi]),
  };
}

export async function saveConfig(partial: Partial<ExtensionConfig>): Promise<void> {
  await chrome.storage.sync.set(partial);
}
