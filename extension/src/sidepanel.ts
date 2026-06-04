import type { BackgroundMessage, BackgroundResponse } from "./types.js";
import { applyDataI18n, getLocale, initI18n, localizeError, t } from "./i18n.js";
import { BusyUiController } from "./busy-ui.js";
import { categoryLabel, type CandidateCategory } from "./candidate-display.js";
import { initSidepanelCandidateUI } from "./sidepanel-candidate-ui.js";
import { watchCandidatesChanged } from "./sidepanel-client.js";

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
  const details = res.errorDetails;
  if (details && details.error === "unsafe_rde_category") {
    const category = String(details.rde_category ?? "unknown");
    if (getLocale() === "ja") {
      return `このCandidateは「${categoryLabel(category as CandidateCategory, "ja")}」と評価されているため、そのまま採用できません。`;
    }
  }
  if (details && typeof details.message === "string") {
    return localizeError(details.message);
  }
  return localizeError(res.error);
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

  await busyUi.run("refreshingCandidates", () => candidateUi!.loadCandidates());

  watchCandidatesChanged((candidateId) => {
    void candidateUi?.loadCandidates(candidateId ?? undefined);
  });
}

void init();
