import type { BackgroundMessage, BackgroundResponse } from "./types.js";
import { formatUserFacingBridgeError } from "./bridge-error-format.js";
import { applyDataI18n, initI18n, t } from "./i18n.js";
import { BusyUiController } from "./busy-ui.js";
import { initSidepanelCandidateUI } from "./sidepanel-candidate-ui.js";
import { STORAGE_KEYS } from "./config.js";
import type { OptionsUpdatedMessage } from "./options-notify.js";
import { peekCandidatesFocusId, watchCandidatesChanged } from "./sidepanel-client.js";

function $(id: string): HTMLElement {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing #${id}`);
  return el;
}

async function send(message: BackgroundMessage): Promise<BackgroundResponse> {
  return chrome.runtime.sendMessage(message) as Promise<BackgroundResponse>;
}

const EVAL_LEVEL_STORAGE_KEY = "sayane.evalLevel";

function normalizeEvalLevel(value: unknown): number {
  const n = Number(value);
  if (!Number.isInteger(n)) return 1;
  return Math.max(1, Math.min(5, n));
}

async function getStoredEvalLevel(): Promise<number> {
  const stored = await chrome.storage.local.get(EVAL_LEVEL_STORAGE_KEY);
  return normalizeEvalLevel(stored[EVAL_LEVEL_STORAGE_KEY]);
}

function formatBridgeError(res: Extract<BackgroundResponse, { ok: false }>): string {
  return formatUserFacingBridgeError(
    res.error,
    res.errorDetails as Record<string, unknown> | undefined,
  );
}

const busyUi = new BusyUiController($("app-root"));

function registerBusyButtons(): void {
  busyUi.registerButton("btn-refresh-candidates", $("btn-refresh-candidates") as HTMLButtonElement, {
    busyKey: "refreshingCandidates",
    idleLabel: "↻",
    busyLabel: t("busy.refreshing"),
  });
}

let candidateUi: ReturnType<typeof initSidepanelCandidateUI> | null = null;

async function init(): Promise<void> {
  await initI18n();
  applyDataI18n();
  registerBusyButtons();
  document.title = t("sidepanel.title");

  const evalLevel = await getStoredEvalLevel();
  candidateUi = initSidepanelCandidateUI({
    $,
    send,
    busyUi,
    formatBridgeError,
    getStoredEvalLevel: () => evalLevel,
  });

  watchCandidatesChanged((candidateId) => {
    if (candidateId) {
      void candidateUi?.focusCandidate(candidateId);
      return;
    }
    void candidateUi?.loadCandidates();
  });

  const initialFocusId = await peekCandidatesFocusId();
  await busyUi.run("refreshingCandidates", async () => {
    if (initialFocusId) {
      await candidateUi!.focusCandidate(initialFocusId);
    } else {
      await candidateUi!.loadCandidates();
    }
  });

  const latestFocusId = await peekCandidatesFocusId();
  if (latestFocusId && latestFocusId !== initialFocusId) {
    await candidateUi!.focusCandidate(latestFocusId);
  }

  chrome.runtime.onMessage.addListener((message: OptionsUpdatedMessage) => {
    if (message?.type === "SAYANE_OPTIONS_UPDATED") {
      void candidateUi?.applyShowDebugUi();
    }
  });

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "sync" || !changes[STORAGE_KEYS.showDebugUi]) return;
    void candidateUi?.applyShowDebugUi();
  });
}

void init();
