import { DEFAULT_BRIDGE_URL, loadConfig, saveConfig, STORAGE_KEYS } from "./config.js";
import { probeBridge } from "./bridge-client.js";

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

function setStatus(text: string, isError = false): void {
  const status = document.getElementById("status");
  if (!status) return;
  status.textContent = text;
  status.className = isError ? "error" : "";
}

function readForm(): { bridgeUrl: string; bridgeToken: string; defaultProfileId: string } {
  return {
    bridgeUrl: input("bridge-url").value.trim() || DEFAULT_BRIDGE_URL,
    bridgeToken: input("bridge-token").value.trim(),
    defaultProfileId: input("default-profile").value.trim() || "default",
  };
}

async function init(): Promise<void> {
  const config = await loadConfig();
  input("bridge-url").value = config.bridgeUrl || DEFAULT_BRIDGE_URL;
  input("bridge-token").value = config.bridgeToken;
  input("default-profile").value = config.defaultProfileId;
}

$("save").addEventListener("click", async () => {
  try {
    const form = readForm();
    await saveConfig({
      [STORAGE_KEYS.bridgeUrl]: form.bridgeUrl,
      [STORAGE_KEYS.bridgeToken]: form.bridgeToken,
      [STORAGE_KEYS.defaultProfileId]: form.defaultProfileId,
    });
    setStatus("Saved.");
  } catch (err) {
    setStatus(String(err), true);
  }
});

$("test-bridge").addEventListener("click", async () => {
  setStatus("Testing connection…");
  try {
    const form = readForm();
    await saveConfig({
      [STORAGE_KEYS.bridgeUrl]: form.bridgeUrl,
      [STORAGE_KEYS.bridgeToken]: form.bridgeToken,
      [STORAGE_KEYS.defaultProfileId]: form.defaultProfileId,
    });
    const result = await probeBridge(form.bridgeUrl, form.bridgeToken);
    setStatus(result.message, !result.ok);
  } catch (err) {
    setStatus(String(err), true);
  }
});

void init().catch((err) => setStatus(String(err), true));
