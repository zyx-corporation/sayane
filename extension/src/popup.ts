import type {
  BackgroundMessage,
  BackgroundResponse,
  ProfileSummary,
  SupportedLocale,
} from "./types.js";
import type { InsertTarget } from "./providers/types.js";
import { listPopupInsertProviders, listPreviewInsertProviders } from "./providers/registry.js";
import { applyDataI18n, getLocale, initI18n, localizeError, normalizeLocale, t } from "./i18n.js";
import { categoryLabel, type CandidateCategory } from "./candidate-display.js";
import {
  openSidePanelOnUserGesture,
  reopenExtensionPopup,
} from "./sidepanel-client.js";
import { BusyUiController, applyDisabledWithCursorHint } from "./busy-ui.js";
import { loadConfig } from "./config.js";
import {
  deriveCaptureAvailability,
  diagnoseActiveTab,
  type BridgeState,
  type CaptureAvailability,
  type PageState,
} from "./page-diagnostics.js";
import { getActiveCaptureTab } from "./tab-target.js";
import type { OptionsUpdatedMessage } from "./options-notify.js";
import {
  analyzeClipboardText,
  buildLargeImportantTermsConfirmMessage,
  parseImportantTermsInCapture,
  shouldConfirmLargeImportantTermsCapture,
} from "./clipboard-preview.js";
import type { ImportantTermsPreflightSummary } from "./types.js";

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

let lastAvailability: CaptureAvailability | null = null;

function renderBridgeState(state: BridgeState): void {
  const el = $("bridge-state");
  if (state.kind === "connected") {
    el.textContent = t("popup.bridge.connected");
  } else if (state.kind === "checking") {
    el.textContent = t("popup.bridge.checking");
  } else if (state.kind === "failed") {
    el.textContent = t("popup.bridge.unreachable");
  } else {
    el.textContent = "";
  }
}

function renderPageStateLine(pageState: PageState): void {
  const el = $("page-state");
  switch (pageState.kind) {
    case "readable":
      el.textContent = t("page.status.readable", { provider: pageState.ping.provider });
      break;
    case "extractor_failed":
      el.textContent = t("page.status.unreadable");
      break;
    case "content_script_unavailable":
      el.textContent = t("page.status.content_script");
      break;
    case "unsupported_url":
      el.textContent = t("page.status.unsupported");
      break;
    case "no_active_tab":
      el.textContent = t("page.status.no_tab");
      break;
    case "checking":
      el.textContent = t("page.status.checking");
      break;
    default:
      el.textContent = "";
  }
}

function formatPageDetail(avail: CaptureAvailability): string {
  const lines: string[] = [t("page.detail.header")];
  const url = avail.tabUrl ?? "-";
  lines.push(t("page.detail.url", { url }));

  const ping =
    avail.pageState.kind === "readable" || avail.pageState.kind === "extractor_failed"
      ? avail.pageState.ping
      : null;

  if (ping) {
    lines.push(t("page.detail.provider", { provider: ping.provider }));
    lines.push(
      t("page.detail.content_script", {
        status: ping.contentScriptReady
          ? t("page.detail.content_script_ok")
          : t("page.detail.content_script_no"),
      }),
    );
    lines.push(t("page.detail.page_readable", { value: String(ping.readable) }));
    lines.push(t("page.detail.selection_length", { length: ping.selectionTextLength }));
    lines.push(
      t("page.detail.host_permission", {
        value: ping.hostPermissionOk ? t("page.detail.host_ok") : t("page.detail.host_ng"),
      }),
    );
    if (!ping.extractorAvailable) {
      lines.push(
        t("page.detail.action", {
          action:
            ping.provider === "chatgpt"
              ? t("page.detail.reload_chatgpt")
              : t("page.detail.reload_tab"),
        }),
      );
    }
  } else if (avail.pageState.kind === "content_script_unavailable") {
    lines.push(t("page.reason.content_script_unavailable"));
    const raw = avail.pageState.lastError ?? "";
    if (raw && !raw.includes("Receiving end does not exist")) {
      lines.push(raw);
    }
    lines.push(t("page.detail.action", { action: t("page.detail.cs_reload") }));
  } else if (avail.pageState.kind === "unsupported_url") {
    lines.push(avail.pageState.reason);
    lines.push(t("page.detail.action", { action: t("page.detail.open_supported") }));
  } else if (avail.pageState.kind === "no_active_tab") {
    lines.push(avail.pageState.reason);
  }

  return lines.join("\n");
}

async function renderDebugPanel(avail: CaptureAvailability): Promise<void> {
  const config = await loadConfig();
  const debugEl = $("debug-lines");
  const header = [`Bridge URL: ${config.bridgeUrl}`, ...avail.debugLines];
  debugEl.textContent = header.join("\n");
}

async function refreshClipboardPreviewHint(): Promise<void> {
  const hintEl = $("capture-clipboard-hint") as HTMLElement;
  try {
    const text = await navigator.clipboard.readText();
    const preview = analyzeClipboardText(text);
    if (preview.importantTermsCount > 0) {
      hintEl.textContent = t("capture.clipboard_preview_terms", {
        count: String(preview.importantTermsCount),
        lines: String(preview.lineCount),
        chars: String(preview.charCount),
      });
      return;
    }
    if (preview.charCount > 0) {
      hintEl.textContent = t("capture.clipboard_preview_generic", {
        lines: String(preview.lineCount),
        chars: String(preview.charCount),
      });
      return;
    }
  } catch {
    /* permission or empty — fall through */
  }
  hintEl.textContent = t("capture.clipboard_hint");
}

function applyCaptureAvailability(avail: CaptureAvailability): void {
  lastAvailability = avail;
  renderBridgeState(avail.bridgeState);
  renderPageStateLine(avail.pageState);

  const detailEl = $("page-state-detail");
  const needsDetail =
    avail.pageState.kind !== "readable" && avail.pageState.kind !== "checking";
  detailEl.textContent = needsDetail ? formatPageDetail(avail) : "";
  detailEl.style.whiteSpace = "pre-wrap";

  ($("capture-selection-hint") as HTMLElement).textContent =
    avail.canCaptureSelection ? "" : (avail.selectionDisabledReason ?? "");
  if (!avail.canCaptureClipboard) {
    ($("capture-clipboard-hint") as HTMLElement).textContent =
      avail.clipboardDisabledReason ?? "";
  } else {
    void refreshClipboardPreviewHint();
  }
  ($("capture-page-disabled-hint") as HTMLElement).textContent =
    avail.canCapturePage ? "" : (avail.pageDisabledReason ?? "");

  const busy = busyUi.isBusy();
  busyUi.applyExternalDisabled("btn-capture-selection", !avail.canCaptureSelection || busy);
  busyUi.applyExternalDisabled("btn-capture-clipboard", !avail.canCaptureClipboard || busy);
  busyUi.applyExternalDisabled("btn-capture-page", !avail.canCapturePage || busy);

  void renderDebugPanel(avail);
}

async function applyDeveloperModeUi(): Promise<void> {
  const config = await loadConfig();
  const panel = $("developer-capture-panel") as HTMLDetailsElement;
  panel.hidden = !config.developerMode;
}

async function applyShowDebugUi(): Promise<void> {
  const config = await loadConfig();
  const show = config.showDebugUi;
  ($("debug-panel") as HTMLDetailsElement).hidden = !show;
  ($("input-debug-actions") as HTMLElement).hidden = !show;
}

async function resolveBridgeState(): Promise<BridgeState> {
  const health = await send({ type: "BRIDGE_HEALTH" });
  if (!health.ok) {
    return { kind: "failed", reason: localizeError(health.error) };
  }
  const healthy = (health.data as { healthy: boolean }).healthy;
  if (!healthy) {
    return { kind: "failed", reason: t("status.bridge_unreachable") };
  }
  return { kind: "connected" };
}

async function runPageDiagnostics(bridgeState: BridgeState): Promise<CaptureAvailability> {
  renderPageStateLine({ kind: "checking" });
  const { pageState, tabId, tabUrl } = await diagnoseActiveTab(t);
  const avail = deriveCaptureAvailability(bridgeState, pageState, tabId, tabUrl, t);
  applyCaptureAvailability(avail);
  return avail;
}

async function reloadSettingsAndDiagnose(): Promise<CaptureAvailability> {
  await loadConfig();
  return runFullDiagnostics();
}

async function runFullDiagnostics(): Promise<CaptureAvailability> {
  renderBridgeState({ kind: "checking" });
  const bridgeState = await resolveBridgeState();
  const avail = await runPageDiagnostics(bridgeState);

  if (bridgeState.kind === "failed") {
    setStatus(bridgeState.reason, true);
  } else if (avail.canCaptureSelection || avail.canCaptureClipboard || avail.canCapturePage) {
    setStatus(t("status.ready"));
  } else {
    setStatus(formatPageDetail(avail), true);
  }
  return avail;
}

async function send(message: BackgroundMessage): Promise<BackgroundResponse> {
  return chrome.runtime.sendMessage(message) as Promise<BackgroundResponse>;
}

let profilesById = new Map<string, ProfileSummary>();
const busyUi = new BusyUiController($("app-root"));
const insertButtons: HTMLButtonElement[] = [];

function registerBusyButtons(): void {
  busyUi.registerButton("btn-capture-selection", $("btn-capture-selection") as HTMLButtonElement, {
    busyKey: "capturing",
    idleLabel: t("capture.selection"),
    busyLabel: t("busy.capturing"),
  });
  busyUi.registerButton("btn-capture-clipboard", $("btn-capture-clipboard") as HTMLButtonElement, {
    busyKey: "capturingClipboard",
    idleLabel: t("capture.clipboard"),
    busyLabel: t("busy.capturing_clipboard"),
  });
  busyUi.registerButton("btn-capture-page", $("btn-capture-page") as HTMLButtonElement, {
    busyKey: "capturing",
    idleLabel: t("capture.page"),
    busyLabel: t("busy.capturing"),
  });
  busyUi.registerButton("btn-bridge-check", $("btn-bridge-check") as HTMLButtonElement, {
    busyKey: "pairing",
    idleLabel: t("bridge.check"),
    busyLabel: t("busy.pairing"),
  });
  for (const btn of insertButtons) {
    const providerId = btn.dataset.providerId ?? "insert";
    busyUi.registerButton(`insert-${providerId}`, btn, {
      busyKey: "insertingContext",
      idleLabel: btn.textContent ?? t("insert.chatgpt"),
      busyLabel: t("busy.inserting"),
    });
  }
}

function setInsertButtonsDisabled(disabled: boolean): void {
  const hint = busyUi.cursorHintForExternalDisabled(disabled);
  for (const btn of insertButtons) {
    if (busyUi.getState().insertingContext) {
      applyDisabledWithCursorHint(btn, true, "busy");
      continue;
    }
    applyDisabledWithCursorHint(btn, disabled, hint);
  }
}

async function checkBridgeHealth(): Promise<boolean> {
  const avail = await runFullDiagnostics();
  return avail.bridgeState.kind === "connected";
}

function selectedProfile(): ProfileSummary | null {
  const id = selectedProfileId();
  return profilesById.get(id) ?? null;
}

function captureLocaleForSave(): SupportedLocale {
  const uiLocale = getLocale() || "en";
  const profileLocale = selectedProfile()?.default_language;
  return profileLocale ? normalizeLocale(profileLocale) : uiLocale;
}

function formatBridgeError(res: Extract<BackgroundResponse, { ok: false }>): string {
  const details = res.errorDetails;
  if (details && details.error === "unsafe_rde_category") {
    const category = String(details.rde_category ?? "unknown");
    if (getLocale() === "ja") {
      return `このCandidateは「${categoryLabel(category as CandidateCategory, "ja")}」と評価されているため、そのまま採用できません。差分を確認し、必要なら修正して新しいCandidateとして作成してください。`;
    }
  }
  if (details && typeof details.message === "string") {
    return localizeError(details.message);
  }
  return localizeError(res.error);
}

async function getCaptureWindowId(): Promise<number | undefined> {
  const win = await chrome.windows.getCurrent();
  return win.id;
}

async function getActiveTabId(): Promise<number> {
  const tab = await getActiveCaptureTab();
  if (!tab?.id) throw new Error(t("error.no_active_tab"));
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
    setStatus(localizeError(res.error), true);
    return;
  }
  const profiles = res.data as ProfileSummary[];
  profilesById = new Map(profiles.map((p) => [p.id, p]));
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

function renderInsertButtons(): void {
  const container = $("insert-providers");
  container.innerHTML = "";

  for (const provider of listPopupInsertProviders()) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.providerId = provider.id;
    btn.dataset.i18n = provider.labelKey;
    btn.textContent = t(provider.labelKey);
    btn.addEventListener("click", () => void insertContext(provider.id));
    insertButtons.push(btn);
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
  registerBusyButtons();
  busyUi.setOnStateChange(() => {
    if (lastAvailability) applyCaptureAvailability(lastAvailability);
    setInsertButtonsDisabled(busyUi.isBusy());
  });
  document.title = t("app.title");
  setStatus(t("status.loading"));
  await applyDeveloperModeUi();

  const avail = await busyUi.run("pairing", () => runFullDiagnostics());

  if (avail.bridgeState.kind !== "connected") return;
  await loadProfiles();
}

$("btn-capture-selection").addEventListener("click", () => {
  openSidePanelOnUserGesture();
  void busyUi.run("capturing", async () => {
    try {
      const tabId = await getActiveTabId();
      const windowId = await getCaptureWindowId();
      const res = await send({
        type: "CAPTURE_SELECTION",
        tabId,
        windowId,
        profileId: selectedProfileId(),
        locale: captureLocaleForSave(),
      });
      if (!res.ok) {
        setStatus(formatBridgeError(res), true);
        return;
      }
      setCaptureStatus(res.data as import("./types.js").CaptureResult, { windowId });
    } catch (e) {
      setStatus(localizeError(String(e)), true);
    }
  });
});

$("btn-capture-page").addEventListener("click", () => {
  openSidePanelOnUserGesture();
  void busyUi.run("capturing", async () => {
    try {
      const tabId = await getActiveTabId();
      const windowId = await getCaptureWindowId();
      const res = await send({
        type: "CAPTURE_PAGE",
        tabId,
        windowId,
        profileId: selectedProfileId(),
        locale: captureLocaleForSave(),
      });
      if (!res.ok) {
        setStatus(formatBridgeError(res), true);
        return;
      }
      setCaptureStatus(res.data as import("./types.js").CaptureResult, {
        pageCapture: true,
        windowId,
      });
    } catch (e) {
      setStatus(localizeError(String(e)), true);
    }
  });
});

$("btn-capture-clipboard").addEventListener("click", () => {
  openSidePanelOnUserGesture();
  void busyUi.run("capturingClipboard", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (!text.trim()) {
        setStatus(t("capture.clipboard_empty"), true);
        return;
      }
      const terms = parseImportantTermsInCapture(text);
      const preview = analyzeClipboardText(text);
      if (shouldConfirmLargeImportantTermsCapture(preview)) {
        let preflight: ImportantTermsPreflightSummary | null = null;
        const preRes = await send({
          type: "BRIDGE_PREFLIGHT_IMPORTANT_TERMS",
          content: text,
          profileId: selectedProfileId(),
        });
        if (preRes.ok && preRes.data) {
          preflight = preRes.data as ImportantTermsPreflightSummary;
        }
        const proceed = globalThis.confirm(
          buildLargeImportantTermsConfirmMessage(preview, preflight, t),
        );
        if (!proceed) {
          setStatus(t("capture.clipboard_confirm_cancelled"));
          void refreshClipboardPreviewHint();
          return;
        }
      }
      const captureWarnings: string[] = [];
      if (terms.length > 8) {
        captureWarnings.push("clipboard_many_important_terms");
      }
      const windowId = await getCaptureWindowId();
      const res = await send({
        type: "CAPTURE_CLIPBOARD",
        content: text,
        windowId,
        profileId: selectedProfileId(),
        locale: captureLocaleForSave(),
        captureWarnings,
      });
      if (!res.ok) {
        setStatus(formatBridgeError(res), true);
        return;
      }
      setCaptureStatus(res.data as import("./types.js").CaptureResult, { windowId });
    } catch {
      setStatus(t("capture.clipboard_error"), true);
    }
  });
});

$("btn-bridge-check").addEventListener("click", () => {
  void busyUi.run("pairing", () => checkBridgeHealth());
});

$("btn-recheck-page").addEventListener("click", () => {
  void busyUi.run("pairing", async () => {
    const avail = await reloadSettingsAndDiagnose();
    if (avail.bridgeState.kind === "connected") {
      await loadProfiles();
      if (avail.canCaptureSelection || avail.canCaptureClipboard || avail.canCapturePage) {
        setStatus(t("status.ready"));
      }
    }
  });
});

chrome.runtime.onMessage.addListener((message: OptionsUpdatedMessage) => {
  if (message?.type === "SAYANE_OPTIONS_UPDATED") {
    void reloadSettingsAndDiagnose().then(async (avail) => {
      if (avail.bridgeState.kind === "connected") {
        await loadProfiles();
        await applyDeveloperModeUi();
        await applyShowDebugUi();
      }
    });
  }
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "sync") return;
  if (changes.developerMode) {
    void applyDeveloperModeUi();
  }
  if (changes.showDebugUi) {
    void applyShowDebugUi();
  }
});

function setCaptureStatus(
  data: import("./types.js").CaptureResult,
  options?: { pageCapture?: boolean; windowId?: number },
): void {
  const id = data.id;
  const warnings = data.warnings ?? [];
  const pageWarn = options?.pageCapture
    ? warnings.includes("page_capture_low_confidence") ||
        warnings.includes("ui_noise_detected")
    : false;
  const fullPersonaWarn = warnings.includes("full_persona_document_detected");
  const manyTermsWarn = warnings.includes("clipboard_many_important_terms");
  const hint = pageWarn
    ? t("capture.warning.page_low_confidence")
    : fullPersonaWarn
      ? t("capture.warning.full_persona_document")
      : manyTermsWarn
        ? t("capture.warning.clipboard_many_important_terms")
        : warnings[0];
  const msg = hint
    ? `${t("status.captured", { id: id.slice(0, 8) })} — ${hint}`
    : t("status.captured", { id: id.slice(0, 8) });
  setStatus(msg, Boolean(hint));
  if (options?.windowId != null) {
    void reopenExtensionPopup(options.windowId);
  }
}

async function insertContext(target: InsertTarget): Promise<void> {
  await busyUi.run("insertingContext", async () => {
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
  });
}

$("btn-open-sidepanel").addEventListener("click", () => {
  openSidePanelOnUserGesture();
});

$("btn-options").addEventListener("click", () => chrome.runtime.openOptionsPage());

void init();
