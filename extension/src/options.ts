import { DEFAULT_BRIDGE_URL, loadConfig, saveConfig, STORAGE_KEYS } from "./config.js";
import { probeBridge } from "./bridge-client.js";
import { applyDataI18n, initI18n, t } from "./i18n.js";
import type { DisplayLanguage } from "./types.js";

function $(id: string): HTMLElement {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing #${id}`);
  return el;
}

function input(id: string): HTMLInputElement {
  const el = $(id);
  if (!(el instanceof HTMLInputElement)) throw new Error(`Not an input: #${id}`);
  return el;
}

function select(id: string): HTMLSelectElement {
  const el = $(id);
  if (!(el instanceof HTMLSelectElement)) throw new Error(`Not a select: #${id}`);
  return el;
}

function setStatus(text: string, isError = false): void {
  const status = document.getElementById("status");
  if (!status) return;
  status.textContent = text;
  status.className = isError ? "error" : "";
}

function readForm(): {
  bridgeUrl: string;
  bridgeToken: string;
  defaultProfileId: string;
  displayLanguage: DisplayLanguage;
} {
  const lang = select("display-language").value;
  const displayLanguage: DisplayLanguage =
    lang === "en" || lang === "ja" || lang === "auto" ? lang : "auto";
  return {
    bridgeUrl: input("bridge-url").value.trim() || DEFAULT_BRIDGE_URL,
    bridgeToken: input("bridge-token").value.trim(),
    defaultProfileId: input("default-profile").value.trim() || "default",
    displayLanguage,
  };
}

async function refreshUiLanguage(): Promise<void> {
  await initI18n();
  applyDataI18n();
  document.title = t("options.title");
}

async function init(): Promise<void> {
  const config = await loadConfig();
  select("display-language").value = config.displayLanguage;
  input("bridge-url").value = config.bridgeUrl || DEFAULT_BRIDGE_URL;
  input("bridge-token").value = config.bridgeToken;
  input("default-profile").value = config.defaultProfileId;
  await refreshUiLanguage();
}

select("display-language").addEventListener("change", () => {
  void refreshUiLanguage();
});

$("save").addEventListener("click", async () => {
  try {
    const form = readForm();
    await saveConfig({
      [STORAGE_KEYS.bridgeUrl]: form.bridgeUrl,
      [STORAGE_KEYS.bridgeToken]: form.bridgeToken,
      [STORAGE_KEYS.defaultProfileId]: form.defaultProfileId,
      [STORAGE_KEYS.displayLanguage]: form.displayLanguage,
    });
    await refreshUiLanguage();
    setStatus(t("options.saved"));
  } catch (err) {
    setStatus(String(err), true);
  }
});

$("test-bridge").addEventListener("click", async () => {
  setStatus(t("options.testing"));
  try {
    const form = readForm();
    await saveConfig({
      [STORAGE_KEYS.bridgeUrl]: form.bridgeUrl,
      [STORAGE_KEYS.bridgeToken]: form.bridgeToken,
      [STORAGE_KEYS.defaultProfileId]: form.defaultProfileId,
      [STORAGE_KEYS.displayLanguage]: form.displayLanguage,
    });
    await refreshUiLanguage();
    const result = await probeBridge(form.bridgeUrl, form.bridgeToken);
    setStatus(t(result.messageKey, result.ok ? undefined : result.params), !result.ok);
  } catch (err) {
    setStatus(String(err), true);
  }
});

void init().catch((err) => setStatus(String(err), true));
