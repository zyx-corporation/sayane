import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateDiff,
  CandidateSummary,
  ProfileSummary,
} from "./types.js";
import type { InsertTarget } from "./providers/types.js";
import { listPopupInsertProviders, listPreviewInsertProviders } from "./providers/registry.js";
import { applyDataI18n, initI18n, localizeError, t } from "./i18n.js";

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
  if (!tab?.id) throw new Error(t("error.no_active_tab"));
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
    setStatus(localizeError(res.error), true);
    return;
  }
  const profiles = res.data as ProfileSummary[];
  select.innerHTML = "";
  if (profiles.length === 0) {
    const opt = document.createElement("option");
    opt.value = "default";
    opt.textContent = t("profile.not_found");
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
    setStatus(localizeError(res.error), true);
    return;
  }
  const items = res.data as CandidateSummary[];
  select.innerHTML = "";
  if (items.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = t("candidate.none");
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

function renderInsertButtons(): void {
  const container = $("insert-providers");
  container.innerHTML = "";

  for (const provider of listPopupInsertProviders()) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.providerId = provider.id;
    btn.dataset.i18n = provider.labelKey;
    btn.textContent = t(provider.labelKey);
    btn.addEventListener("click", () => insertContext(provider.id));
    container.appendChild(btn);
  }

  const preview = listPreviewInsertProviders();
  if (preview.length === 0) return;

  const details = document.createElement("details");
  details.className = "insert-preview-collapsible";

  const summary = document.createElement("summary");
  summary.dataset.i18n = "insert.preview_toggle";
  summary.textContent = t("insert.preview_toggle");
  details.appendChild(summary);

  const hint = document.createElement("p");
  hint.className = "insert-preview";
  hint.dataset.i18n = "insert.preview_note";
  hint.textContent = t("insert.preview_note");
  details.appendChild(hint);

  const list = document.createElement("ul");
  list.className = "insert-preview-list";
  for (const provider of preview) {
    const item = document.createElement("li");
    item.dataset.i18n = provider.labelKey;
    item.textContent = t(provider.labelKey);
    list.appendChild(item);
  }
  details.appendChild(list);
  container.appendChild(details);
}

async function init(): Promise<void> {
  await initI18n();
  applyDataI18n();
  renderInsertButtons();
  applyDataI18n($("insert-providers"));
  document.title = t("app.title");
  setStatus(t("status.loading"));

  const health = await send({ type: "BRIDGE_HEALTH" });
  if (!health.ok) {
    setStatus(localizeError(health.error), true);
    return;
  }
  const healthy = (health.data as { healthy: boolean }).healthy;
  if (!healthy) {
    setStatus(t("status.bridge_unreachable"), true);
    return;
  }
  setStatus(t("status.bridge_connected"));
  await loadProfiles();
  await loadCandidates();
}

$("btn-capture-selection").addEventListener("click", async () => {
  try {
    const tabId = await getActiveTabId();
    const res = await send({ type: "CAPTURE_SELECTION", tabId });
    if (!res.ok) {
      setStatus(localizeError(res.error), true);
      return;
    }
    setCaptureStatus(res.data as import("./types.js").CaptureResult);
  } catch (e) {
    setStatus(localizeError(String(e)), true);
  }
});

$("btn-capture-page").addEventListener("click", async () => {
  try {
    const tabId = await getActiveTabId();
    const res = await send({ type: "CAPTURE_PAGE", tabId });
    if (!res.ok) {
      setStatus(localizeError(res.error), true);
      return;
    }
    setCaptureStatus(res.data as import("./types.js").CaptureResult);
  } catch (e) {
    setStatus(localizeError(String(e)), true);
  }
});

function setCaptureStatus(data: import("./types.js").CaptureResult): void {
  const id = data.id;
  const warn = data.warnings?.[0];
  const msg = warn
    ? `${t("status.captured", { id: id.slice(0, 8) })} — ${warn}`
    : t("status.captured", { id: id.slice(0, 8) });
  setStatus(msg, Boolean(warn));
  void loadCandidates(id);
}

async function insertContext(target: InsertTarget): Promise<void> {
  try {
    const tabId = await getActiveTabId();
    const res = await send({
      type: "INSERT_CONTEXT_PACKET",
      tabId,
      target,
      profileId: selectedProfileId(),
    });
    setStatus(res.ok ? t("status.inserted", { target }) : localizeError(res.error), !res.ok);
  } catch (e) {
    setStatus(localizeError(String(e)), true);
  }
}

$("btn-refresh-candidates").addEventListener("click", async () => {
  try {
    await loadCandidates(selectedCandidateId() ?? undefined);
    setStatus(t("status.candidates_refreshed"));
  } catch (e) {
    setStatus(localizeError(String(e)), true);
  }
});

$("btn-evaluate").addEventListener("click", async () => {
  const cid = selectedCandidateId();
  if (!cid) {
    setStatus(t("status.select_candidate"), true);
    return;
  }
  const level = Number(($("eval-level") as HTMLSelectElement).value) || 1;
  try {
    const res = await send({ type: "BRIDGE_EVALUATE_CANDIDATE", candidateId: cid, level });
    setStatus(
      res.ok
        ? t("status.evaluated", { summary: evaluationSummary(res.data as Record<string, unknown>) })
        : localizeError(res.error),
      !res.ok,
    );
    if (res.ok) await loadCandidates(cid);
  } catch (e) {
    setStatus(localizeError(String(e)), true);
  }
});

$("btn-diff").addEventListener("click", async () => {
  const cid = selectedCandidateId();
  if (!cid) {
    setStatus(t("status.select_candidate"), true);
    return;
  }
  try {
    const res = await send({ type: "BRIDGE_DIFF_CANDIDATE", candidateId: cid });
    if (!res.ok) {
      setStatus(localizeError(res.error), true);
      return;
    }
    showDiff(res.data as CandidateDiff);
    setStatus(t("status.diff_for", { id: cid.slice(0, 8) }));
  } catch (e) {
    setStatus(localizeError(String(e)), true);
  }
});

$("btn-approve").addEventListener("click", async () => {
  const cid = selectedCandidateId();
  if (!cid) {
    setStatus(t("status.select_candidate"), true);
    return;
  }
  try {
    const res = await send({ type: "BRIDGE_APPROVE_CANDIDATE", candidateId: cid });
    setStatus(res.ok ? t("status.approved", { id: cid.slice(0, 8) }) : localizeError(res.error), !res.ok);
    if (res.ok) await loadCandidates(cid);
  } catch (e) {
    setStatus(localizeError(String(e)), true);
  }
});

$("btn-reject").addEventListener("click", async () => {
  const cid = selectedCandidateId();
  if (!cid) {
    setStatus(t("status.select_candidate"), true);
    return;
  }
  try {
    const res = await send({
      type: "BRIDGE_REJECT_CANDIDATE",
      candidateId: cid,
      reason: "rejected from extension",
    });
    setStatus(res.ok ? t("status.rejected", { id: cid.slice(0, 8) }) : localizeError(res.error), !res.ok);
    if (res.ok) await loadCandidates(cid);
  } catch (e) {
    setStatus(localizeError(String(e)), true);
  }
});

$("btn-options").addEventListener("click", () => chrome.runtime.openOptionsPage());

void init();
