import type { BackgroundMessage, BackgroundResponse, InsertTarget, ProfileSummary } from "./types.js";

function $(id: string): HTMLElement {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing #${id}`);
  return el;
}

function setStatus(text: string, isError = false): void {
  const el = $("status");
  el.textContent = text;
  el.className = isError ? "status error" : "status";
}

async function send(message: BackgroundMessage): Promise<BackgroundResponse> {
  return chrome.runtime.sendMessage(message) as Promise<BackgroundResponse>;
}

async function getActiveTabId(): Promise<number> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("No active tab");
  return tab.id;
}

function selectedProfileId(): string {
  const select = $("profile-select") as HTMLSelectElement;
  return select.value || "default";
}

async function loadProfiles(): Promise<void> {
  const select = $("profile-select") as HTMLSelectElement;
  const res = await send({ type: "BRIDGE_LIST_PROFILES" });
  if (!res.ok) {
    setStatus(res.error, true);
    return;
  }
  const profiles = res.data as ProfileSummary[];
  select.innerHTML = "";
  if (profiles.length === 0) {
    const opt = document.createElement("option");
    opt.value = "default";
    opt.textContent = "default (not found)";
    select.appendChild(opt);
    return;
  }
  for (const p of profiles) {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name ? `${p.id} — ${p.name}` : p.id;
    select.appendChild(opt);
  }
}

async function init(): Promise<void> {
  const health = await send({ type: "BRIDGE_HEALTH" });
  if (!health.ok) {
    setStatus(health.error, true);
    return;
  }
  const healthy = (health.data as { healthy: boolean }).healthy;
  if (!healthy) {
    setStatus("Bridge unreachable. Run: omomuki serve", true);
    return;
  }
  setStatus("Bridge connected");
  await loadProfiles();
}

$("btn-capture-selection").addEventListener("click", async () => {
  try {
    const tabId = await getActiveTabId();
    const res = await send({ type: "CAPTURE_SELECTION", tabId });
    setStatus(res.ok ? `Captured: ${(res.data as { id: string }).id}` : res.error, !res.ok);
  } catch (e) {
    setStatus(String(e), true);
  }
});

$("btn-capture-page").addEventListener("click", async () => {
  try {
    const tabId = await getActiveTabId();
    const res = await send({ type: "CAPTURE_PAGE", tabId });
    setStatus(res.ok ? `Captured: ${(res.data as { id: string }).id}` : res.error, !res.ok);
  } catch (e) {
    setStatus(String(e), true);
  }
});

async function insertContext(target: InsertTarget): Promise<void> {
  try {
    const tabId = await getActiveTabId();
    const res = await send({
      type: "INSERT_CONTEXT_PACKET",
      tabId,
      target,
      profileId: selectedProfileId(),
    });
    setStatus(res.ok ? `Inserted (${target})` : res.error, !res.ok);
  } catch (e) {
    setStatus(String(e), true);
  }
}

$("btn-insert-chatgpt").addEventListener("click", () => insertContext("chatgpt"));
$("btn-insert-claude").addEventListener("click", () => insertContext("claude"));

$("btn-options").addEventListener("click", () => chrome.runtime.openOptionsPage());

void init();
