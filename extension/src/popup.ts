import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateDiff,
  CandidateSummary,
  InsertTarget,
  ProfileSummary,
} from "./types.js";

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

function selectedCandidateId(): string | null {
  const select = $("candidate-select") as HTMLSelectElement;
  return select.value || null;
}

function selectCandidateById(id: string): void {
  const select = $("candidate-select") as HTMLSelectElement;
  for (let i = 0; i < select.options.length; i++) {
    const opt = select.options.item(i);
    if (opt?.value === id) {
      select.value = id;
      return;
    }
  }
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

async function loadCandidates(preferId?: string): Promise<void> {
  const select = $("candidate-select") as HTMLSelectElement;
  const res = await send({ type: "BRIDGE_LIST_CANDIDATES" });
  if (!res.ok) {
    setStatus(res.error, true);
    return;
  }
  const items = res.data as CandidateSummary[];
  select.innerHTML = "";
  if (items.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "(no candidates)";
    select.appendChild(opt);
    return;
  }
  for (const c of items) {
    const opt = document.createElement("option");
    opt.value = c.id;
    const rde = c.rde_class ? ` · ${c.rde_class}` : "";
    opt.textContent = `${c.id.slice(0, 8)}… · ${c.status}${rde}`;
    select.appendChild(opt);
  }
  if (preferId) selectCandidateById(preferId);
}

function showDiff(diff: CandidateDiff): void {
  const pre = $("diff-preview") as HTMLPreElement;
  pre.hidden = false;
  pre.textContent = JSON.stringify(diff, null, 2);
}

function evaluationSummary(data: Record<string, unknown>): string {
  const ev = data.evaluation as { rde_class?: string; level?: number } | undefined;
  if (ev?.rde_class) return `${ev.rde_class} (L${ev.level ?? "?"})`;
  return String(data.status ?? "ok");
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
  await loadCandidates();
}

$("btn-capture-selection").addEventListener("click", async () => {
  try {
    const tabId = await getActiveTabId();
    const res = await send({ type: "CAPTURE_SELECTION", tabId });
    if (!res.ok) {
      setStatus(res.error, true);
      return;
    }
    const id = (res.data as { id: string }).id;
    setStatus(`Captured: ${id}`);
    await loadCandidates(id);
  } catch (e) {
    setStatus(String(e), true);
  }
});

$("btn-capture-page").addEventListener("click", async () => {
  try {
    const tabId = await getActiveTabId();
    const res = await send({ type: "CAPTURE_PAGE", tabId });
    if (!res.ok) {
      setStatus(res.error, true);
      return;
    }
    const id = (res.data as { id: string }).id;
    setStatus(`Captured: ${id}`);
    await loadCandidates(id);
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

$("btn-refresh-candidates").addEventListener("click", async () => {
  try {
    await loadCandidates(selectedCandidateId() ?? undefined);
    setStatus("Candidates refreshed");
  } catch (e) {
    setStatus(String(e), true);
  }
});

$("btn-evaluate").addEventListener("click", async () => {
  const cid = selectedCandidateId();
  if (!cid) {
    setStatus("Select a candidate", true);
    return;
  }
  const level = Number(($("eval-level") as HTMLSelectElement).value) || 1;
  try {
    const res = await send({ type: "BRIDGE_EVALUATE_CANDIDATE", candidateId: cid, level });
    setStatus(res.ok ? `Evaluated: ${evaluationSummary(res.data as Record<string, unknown>)}` : res.error, !res.ok);
    if (res.ok) await loadCandidates(cid);
  } catch (e) {
    setStatus(String(e), true);
  }
});

$("btn-diff").addEventListener("click", async () => {
  const cid = selectedCandidateId();
  if (!cid) {
    setStatus("Select a candidate", true);
    return;
  }
  try {
    const res = await send({ type: "BRIDGE_DIFF_CANDIDATE", candidateId: cid });
    if (!res.ok) {
      setStatus(res.error, true);
      return;
    }
    showDiff(res.data as CandidateDiff);
    setStatus(`Diff for ${cid.slice(0, 8)}…`);
  } catch (e) {
    setStatus(String(e), true);
  }
});

$("btn-approve").addEventListener("click", async () => {
  const cid = selectedCandidateId();
  if (!cid) {
    setStatus("Select a candidate", true);
    return;
  }
  try {
    const res = await send({ type: "BRIDGE_APPROVE_CANDIDATE", candidateId: cid });
    setStatus(res.ok ? `Approved: ${cid.slice(0, 8)}…` : res.error, !res.ok);
    if (res.ok) await loadCandidates(cid);
  } catch (e) {
    setStatus(String(e), true);
  }
});

$("btn-reject").addEventListener("click", async () => {
  const cid = selectedCandidateId();
  if (!cid) {
    setStatus("Select a candidate", true);
    return;
  }
  try {
    const res = await send({
      type: "BRIDGE_REJECT_CANDIDATE",
      candidateId: cid,
      reason: "rejected from extension",
    });
    setStatus(res.ok ? `Rejected: ${cid.slice(0, 8)}…` : res.error, !res.ok);
    if (res.ok) await loadCandidates(cid);
  } catch (e) {
    setStatus(String(e), true);
  }
});

$("btn-options").addEventListener("click", () => chrome.runtime.openOptionsPage());

void init();
