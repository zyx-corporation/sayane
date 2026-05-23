import { DEFAULT_BRIDGE_URL, loadConfig, saveConfig, STORAGE_KEYS } from "./config.js";
import { checkHealth } from "./bridge-client.js";

function $(id: string): HTMLInputElement {
  const el = document.getElementById(id);
  if (!(el instanceof HTMLInputElement)) throw new Error(`Missing #${id}`);
  return el;
}

async function init(): Promise<void> {
  const config = await loadConfig();
  $("bridge-url").value = config.bridgeUrl || DEFAULT_BRIDGE_URL;
  $("bridge-token").value = config.bridgeToken;
  $("default-profile").value = config.defaultProfileId;
}

$("save").addEventListener("click", async () => {
  const status = document.getElementById("status");
  await saveConfig({
    [STORAGE_KEYS.bridgeUrl]: $("bridge-url").value.trim() || DEFAULT_BRIDGE_URL,
    [STORAGE_KEYS.bridgeToken]: $("bridge-token").value.trim(),
    [STORAGE_KEYS.defaultProfileId]: $("default-profile").value.trim() || "default",
  });
  if (status) status.textContent = "Saved.";
});

$("test-bridge").addEventListener("click", async () => {
  const status = document.getElementById("status");
  await saveConfig({
    [STORAGE_KEYS.bridgeUrl]: $("bridge-url").value.trim(),
    [STORAGE_KEYS.bridgeToken]: $("bridge-token").value.trim(),
  });
  const ok = await checkHealth();
  if (status) {
    status.textContent = ok ? "Bridge /health OK" : "Bridge unreachable";
    status.className = ok ? "" : "error";
  }
});

void init();
