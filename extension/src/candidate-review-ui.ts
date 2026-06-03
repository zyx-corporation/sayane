/**
 * Popup candidate list → detail review UI (RDE aids, not auto-decisions).
 */

import {
  canApprove,
  canApproveWithCriticalOverride,
  canEvaluate,
  canReject,
  categoryLabel,
  isKnownRdeCategory,
  rdeCssClass,
  rdeSeverity,
  statusCssClass,
  statusWithJudgeLabel,
  type CandidateCategory,
} from "./candidate-display.js";
import type { BusyUiController } from "./busy-ui.js";
import { getLocale, localizeError, t } from "./i18n.js";
import { formatEvaluationNote } from "./rde-notes.js";
import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateDetail,
  CandidateDiff,
  CandidateSummary,
  SupportedLocale,
} from "./types.js";

const KNOWN_SECTIONS = new Set([
  "knowledge.concepts",
  "major_projects",
  "writing_style",
  "project_context",
  "communication_mode",
  "canonical_terms",
  "organization.name",
  "review_required",
  "mixed_sections",
]);

const UIB_LABELS: Record<string, { label: string; titleKey: string }> = {
  UD: { label: "UD", titleKey: "uib.UD.description" },
  MI: { label: "MI", titleKey: "uib.MI.description" },
  CH: { label: "CH", titleKey: "uib.CH.description" },
  DT: { label: "DT", titleKey: "uib.DT.description" },
  VP: { label: "VP", titleKey: "uib.VP.description" },
  FG: { label: "FG", titleKey: "uib.FG.description" },
};

export type CandidateReviewDeps = {
  $: (id: string) => HTMLElement;
  send: (message: BackgroundMessage) => Promise<BackgroundResponse>;
  busyUi: BusyUiController;
  formatBridgeError: (res: Extract<BackgroundResponse, { ok: false }>) => string;
  evaluationSummary: (data: Record<string, unknown>) => string;
  onEvalLevelChange: (level: number) => void;
  getStoredEvalLevel: () => number;
};

export function initCandidateReviewUI(deps: CandidateReviewDeps): {
  loadCandidates: (preferId?: string) => Promise<void>;
  showListView: () => void;
} {
  const { $, send, busyUi, formatBridgeError, evaluationSummary, onEvalLevelChange, getStoredEvalLevel } =
    deps;

  let currentCandidateId: string | null = null;
  let diffLoadedForCandidateId: string | null = null;
  let currentDetail: CandidateDetail | null = null;

  function locale(): SupportedLocale {
    return getLocale();
  }

  function setDetailStatus(text: string, isError = false): void {
    const el = $("detail-status-msg");
    el.textContent = text;
    el.className = isError ? "status error" : "status";
  }

  function showListView(): void {
    currentCandidateId = null;
    currentDetail = null;
    $("view-list").hidden = false;
    $("view-detail").hidden = true;
    void loadCandidates();
  }

  function showDetailView(): void {
    $("view-list").hidden = true;
    $("view-detail").hidden = false;
  }

  function resetDetailFormState(): void {
    ($("reject-reason") as HTMLInputElement).value = "";
    ($("critical-override-reason") as HTMLInputElement).value = "";
    ($("critical-override-check") as HTMLInputElement).checked = false;
    setDetailStatus("");
    $("evaluation-panel").hidden = true;
    $("llm-review-panel").hidden = true;
    $("critical-override-panel").hidden = true;
    $("section-warning").hidden = true;
    $("section-warning").textContent = "";
    $("detail-diff").textContent = "";
    diffLoadedForCandidateId = null;
    const diffDetails = $("diff-details") as HTMLDetailsElement;
    diffDetails.open = false;
  }

  function formatDetailSource(c: CandidateDetail): string {
    const rawSource = (c as unknown as Record<string, unknown>).source;
    if (rawSource && typeof rawSource === "object") {
      const nested = rawSource as { type?: string; uri?: string | null };
      const type = nested.type ?? "";
      const uri = nested.uri ?? null;
      return uri ? `${type} — ${uri}` : type;
    }
    return c.source_url ? `${c.source} — ${c.source_url}` : c.source;
  }

  function formatDetailCapturedAt(c: CandidateDetail): string {
    if (c.captured_at) return c.captured_at;
    const rawSource = (c as unknown as Record<string, unknown>).source;
    if (rawSource && typeof rawSource === "object") {
      const captured = (rawSource as { captured_at?: string }).captured_at;
      if (captured) return captured;
    }
    return "";
  }

  function formatRelativeTime(isoDate: string): string {
    const d = new Date(isoDate);
    const time = d.getTime();
    if (Number.isNaN(time)) return isoDate;

    const diffMin = Math.floor((Date.now() - time) / 60000);
    if (diffMin < 1) return t("time.just_now");
    if (diffMin < 60) return t("time.minutes_ago", { n: diffMin });
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return t("time.hours_ago", { n: diffH });
    return t("time.days_ago", { n: Math.floor(diffH / 24) });
  }

  function renderRdeBadge(el: HTMLElement, rdeClass: string | null | undefined): void {
    if (!rdeClass) {
      el.hidden = true;
      el.textContent = "";
      el.className = "rde-badge";
      return;
    }
    const loc = locale();
    el.hidden = false;
    el.className = `rde-badge ${rdeCssClass(rdeClass)}`;
    el.textContent = isKnownRdeCategory(rdeClass)
      ? categoryLabel(rdeClass, loc)
      : t("rde.unknown");
    el.title = rdeClass;
  }

  function sortCandidates(items: CandidateSummary[]): CandidateSummary[] {
    return [...items].sort((a, b) => {
      const aResolved = a.status === "approved" || a.status === "rejected";
      const bResolved = b.status === "approved" || b.status === "rejected";
      if (aResolved !== bResolved) return aResolved ? 1 : -1;

      const ra = rdeSeverity(a.rde_class);
      const rb = rdeSeverity(b.rde_class);
      if (ra !== rb) return rb - ra;

      return new Date(b.captured_at).getTime() - new Date(a.captured_at).getTime();
    });
  }

  function createCandidateCard(c: CandidateSummary): HTMLButtonElement {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "candidate-card";
    card.dataset.candidateId = c.id;

    const header = document.createElement("div");
    header.className = "card-header";

    const status = document.createElement("span");
    status.className = `status-badge ${statusCssClass(c.status)}`;
    status.textContent = statusWithJudgeLabel(c.status, c.evaluation_status, locale());
    header.appendChild(status);

    if (c.rde_class) {
      const rde = document.createElement("span");
      rde.className = `rde-badge ${rdeCssClass(c.rde_class)}`;
      rde.textContent = categoryLabel(c.rde_class, locale());
      header.appendChild(rde);
    }

    const section = document.createElement("span");
    section.className = "card-section";
    section.textContent = `${c.target_profile_id}:${c.section ?? ""}`;
    header.appendChild(section);

    const preview = document.createElement("div");
    preview.className = "card-preview";
    preview.textContent = c.content_preview ?? "";

    const meta = document.createElement("div");
    meta.className = "card-meta";
    const id = document.createElement("span");
    id.className = "card-id";
    id.textContent = c.id.slice(0, 12);
    meta.appendChild(id);
    meta.appendChild(document.createTextNode(` · ${formatRelativeTime(c.captured_at)}`));

    card.appendChild(header);
    card.appendChild(preview);
    card.appendChild(meta);
    card.addEventListener("click", () => void openCandidateDetail(c.id));
    return card;
  }

  async function loadCandidates(_preferId?: string): Promise<void> {
    const container = $("candidate-list");
    const res = await send({ type: "BRIDGE_LIST_CANDIDATES" });
    if (!res.ok) {
      container.textContent = "";
      const p = document.createElement("p");
      p.className = "no-candidates";
      p.textContent = localizeError(res.error);
      container.appendChild(p);
      return;
    }

    const items = res.data as CandidateSummary[];
    container.textContent = "";
    if (items.length === 0) {
      const p = document.createElement("p");
      p.className = "no-candidates";
      p.textContent = t("candidate.none");
      container.appendChild(p);
      return;
    }

    for (const c of sortCandidates(items)) {
      container.appendChild(createCandidateCard(c));
    }
  }

  function renderSectionWarning(c: CandidateDetail): void {
    const warning = $("section-warning");
    const section = c.proposal.section;
    if (!KNOWN_SECTIONS.has(section)) {
      warning.hidden = false;
      warning.textContent = t("detail.unknown_section_warning", { section });
      return;
    }
    warning.hidden = true;
    warning.textContent = "";
  }

  function configureCriticalOverride(c: CandidateDetail): void {
    const panel = $("critical-override-panel");
    const needsOverride = c.evaluation?.rde_class === "Critical Distortion";
    panel.hidden = !needsOverride;
  }

  function uibBarColor(value: number): string {
    if (value >= 0.7) return "#78909c";
    if (value >= 0.4) return "#90a4ae";
    return "#b0bec5";
  }

  function renderUIBChart(uib: Record<string, number>): void {
    const container = $("uib-chart");
    container.textContent = "";
    for (const [key, meta] of Object.entries(UIB_LABELS)) {
      const raw = uib[key];
      const safeValue = Math.max(0, Math.min(1, typeof raw === "number" ? raw : 0));
      const pct = Math.round(safeValue * 100);

      const labelEl = document.createElement("span");
      labelEl.className = "uib-label";
      labelEl.textContent = meta.label;
      labelEl.title = t(meta.titleKey);

      const barBg = document.createElement("div");
      barBg.className = "uib-bar-bg";
      barBg.title = t(meta.titleKey);

      const barFill = document.createElement("div");
      barFill.className = "uib-bar-fill";
      barFill.style.width = `${pct}%`;
      barFill.style.background = uibBarColor(safeValue);
      barBg.appendChild(barFill);

      const valueEl = document.createElement("span");
      valueEl.className = "uib-value";
      valueEl.textContent = safeValue.toFixed(2);

      container.appendChild(labelEl);
      container.appendChild(barBg);
      container.appendChild(valueEl);
    }
  }

  function renderProposal(proposal: CandidateDetail["proposal"]): void {
    const list = $("detail-proposal-items");
    list.textContent = "";
    for (const item of proposal.add ?? []) {
      const li = document.createElement("li");
      li.textContent = typeof item === "string" ? item : String(item);
      list.appendChild(li);
    }
    const summary = $("detail-proposal-summary");
    const text = proposal.summary ?? "";
    summary.textContent = text;
    summary.hidden = !text;
  }

  function renderEvaluation(ev: NonNullable<CandidateDetail["evaluation"]>): void {
    renderRdeBadge($("eval-rde-class"), ev.rde_class);
    $("eval-level").textContent = `Level ${ev.level}`;
    if (ev.uib) renderUIBChart(ev.uib);

    const notesList = $("eval-notes");
    notesList.textContent = "";
    for (const note of ev.notes ?? []) {
      const payload =
        typeof note === "string"
          ? note
          : {
              source: note.source,
              key: note.key,
              params: note.params as Record<string, string | number | boolean | null> | undefined,
              text: note.text,
            };
      const line = formatEvaluationNote(payload, locale());
      if (!line) continue;
      const li = document.createElement("li");
      li.textContent = line;
      notesList.appendChild(li);
    }

    if (ev.llm_review) {
      $("llm-review-panel").hidden = false;
      $("llm-model").textContent = `${ev.llm_review.model} (L${ev.llm_review.level})`;
      const llmNotes = $("llm-notes");
      llmNotes.textContent = "";
      for (const note of ev.llm_review.notes ?? []) {
        const line = formatEvaluationNote(
          typeof note === "string" ? note : String(note),
          locale(),
        );
        if (!line) continue;
        const li = document.createElement("li");
        li.textContent = line;
        llmNotes.appendChild(li);
      }
    } else {
      $("llm-review-panel").hidden = true;
    }
  }

  function diffLineText(item: unknown): string {
    if (typeof item === "string") return item;
    if (item && typeof item === "object") {
      const o = item as Record<string, unknown>;
      if (typeof o.name === "string") return o.name;
      if (typeof o.summary === "string") return o.summary;
      if (typeof o.value === "string") return o.value;
      if (typeof o.path === "string") return o.path;
    }
    return String(item);
  }

  async function renderDiff(candidateId: string): Promise<void> {
    const container = $("detail-diff");
    container.textContent = t("status.loading");

    const res = await send({ type: "BRIDGE_DIFF_CANDIDATE", candidateId });
    if (!res.ok) {
      container.textContent = "";
      const p = document.createElement("p");
      p.className = "diff-note";
      p.textContent = formatBridgeError(res);
      container.appendChild(p);
      return;
    }

    const diff = res.data as CandidateDiff;
    container.textContent = "";

    if (typeof diff.note === "string" && diff.note) {
      const noteEl = document.createElement("p");
      noteEl.className = "diff-note";
      noteEl.textContent = diff.note;
      container.appendChild(noteEl);
    }

    const addItems = (diff.add ?? diff.proposed_add ?? []) as unknown[];
    const present = (diff.already_present ?? []) as unknown[];

    for (const item of addItems) {
      const line = document.createElement("div");
      line.className = "diff-add";
      line.textContent = diffLineText(item);
      container.appendChild(line);
    }
    for (const item of present) {
      const line = document.createElement("div");
      line.className = "diff-present";
      line.textContent = diffLineText(item);
      container.appendChild(line);
    }

    if (addItems.length === 0 && present.length === 0 && !diff.note) {
      container.textContent = t("detail.diff_empty");
    }
  }

  function updateDetailActionState(c: CandidateDetail): void {
    const category = (c.evaluation?.rde_class ?? null) as CandidateCategory | null;
    const mutationBusy = busyUi.shouldDisableCandidateActions();
    busyUi.applyExternalDisabled(
      "btn-detail-evaluate",
      mutationBusy || !canEvaluate(c.status),
    );
    busyUi.applyExternalDisabled("btn-detail-reject", mutationBusy || !canReject(c.status));
    const canApproveAction = canApproveWithCriticalOverride(c.status, category);
    busyUi.applyExternalDisabled("btn-detail-approve", mutationBusy || !canApproveAction);
  }

  async function openCandidateDetail(candidateId: string): Promise<void> {
    currentCandidateId = candidateId;
    resetDetailFormState();
    showDetailView();
    setDetailStatus(t("status.loading"));

    const res = await send({ type: "BRIDGE_GET_CANDIDATE", candidateId });
    if (!res.ok) {
      setDetailStatus(formatBridgeError(res), true);
      return;
    }

    const c = res.data as CandidateDetail;
    currentCandidateId = c.id;
    currentDetail = c;

    $("detail-id").textContent = c.id;
    $("detail-status").textContent = statusWithJudgeLabel(
      c.status,
      c.evaluation_status,
      locale(),
    );
    renderRdeBadge($("detail-rde-badge"), c.evaluation?.rde_class ?? null);
    $("detail-section").textContent = c.proposal.section;
    $("detail-source").textContent = formatDetailSource(c);
    $("detail-captured-at").textContent = formatRelativeTime(formatDetailCapturedAt(c));
    ($("detail-content") as HTMLPreElement).textContent = c.content;

    renderSectionWarning(c);
    renderProposal(c.proposal);

    if (c.evaluation) {
      renderEvaluation(c.evaluation);
      $("evaluation-panel").hidden = false;
    }

    const levelSelect = $("detail-eval-level") as HTMLSelectElement;
    levelSelect.value = String(c.evaluation?.level ?? getStoredEvalLevel());

    configureCriticalOverride(c);
    updateDetailActionState(c);
    setDetailStatus("");
  }

  $("btn-back").addEventListener("click", () => showListView());

  $("diff-details").addEventListener("toggle", () => {
    if (!currentCandidateId) return;
    const details = $("diff-details") as HTMLDetailsElement;
    if (!details.open) return;
    if (diffLoadedForCandidateId === currentCandidateId) return;
    void renderDiff(currentCandidateId).then(() => {
      diffLoadedForCandidateId = currentCandidateId;
    });
  });

  $("btn-detail-evaluate").addEventListener("click", () => {
    if (!currentCandidateId) return;
    const level = Number(($("detail-eval-level") as HTMLSelectElement).value) || 1;
    void busyUi.run("evaluating", async () => {
      setDetailStatus(t("status.loading"));
      const res = await send({
        type: "BRIDGE_EVALUATE_CANDIDATE",
        candidateId: currentCandidateId!,
        level,
      });
      if (!res.ok) {
        setDetailStatus(formatBridgeError(res), true);
        return;
      }
      setDetailStatus(
        t("status.evaluated", {
          summary: evaluationSummary(res.data as Record<string, unknown>),
        }),
      );
      diffLoadedForCandidateId = null;
      await openCandidateDetail(currentCandidateId!);
    });
  });

  $("btn-detail-approve").addEventListener("click", () => {
    if (!currentCandidateId) return;
    const overridePanelVisible = !$("critical-override-panel").hidden;
    const overrideChecked = ($("critical-override-check") as HTMLInputElement).checked;
    const overrideReason = ($("critical-override-reason") as HTMLInputElement).value.trim();

    if (overridePanelVisible) {
      if (!overrideChecked) {
        setDetailStatus(t("detail.critical_override_required"), true);
        return;
      }
      if (!overrideReason) {
        setDetailStatus(t("detail.critical_override_reason_required"), true);
        return;
      }
      if (!window.confirm(t("detail.critical_override_confirm_dialog"))) return;
    } else if (currentDetail) {
      const cat = currentDetail.evaluation?.rde_class ?? null;
      if (cat && !canApprove(currentDetail.status, cat as CandidateCategory)) {
        setDetailStatus(formatBridgeError({
          ok: false,
          error: "unsafe_rde_category",
          errorDetails: { rde_category: cat },
        }), true);
        return;
      }
    }

    void busyUi.run("approving", async () => {
      const res = await send({
        type: "BRIDGE_APPROVE_CANDIDATE",
        candidateId: currentCandidateId!,
        forceCritical: overridePanelVisible && overrideChecked,
        overrideReason: overridePanelVisible ? overrideReason : undefined,
      });
      if (!res.ok) {
        setDetailStatus(formatBridgeError(res), true);
        return;
      }
      setDetailStatus(t("status.approved", { id: currentCandidateId!.slice(0, 8) }));
      diffLoadedForCandidateId = null;
      await openCandidateDetail(currentCandidateId!);
    });
  });

  $("btn-detail-reject").addEventListener("click", () => {
    if (!currentCandidateId) return;
    const reason = ($("reject-reason") as HTMLInputElement).value.trim() || undefined;
    void busyUi.run("rejecting", async () => {
      const res = await send({
        type: "BRIDGE_REJECT_CANDIDATE",
        candidateId: currentCandidateId!,
        reason,
      });
      if (!res.ok) {
        setDetailStatus(formatBridgeError(res), true);
        return;
      }
      setDetailStatus(t("status.rejected", { id: currentCandidateId!.slice(0, 8) }));
      diffLoadedForCandidateId = null;
      await openCandidateDetail(currentCandidateId!);
    });
  });

  ($("detail-eval-level") as HTMLSelectElement).addEventListener("change", () => {
    const level = Number(($("detail-eval-level") as HTMLSelectElement).value) || 1;
    onEvalLevelChange(level);
  });

  $("btn-refresh-candidates").addEventListener("click", () => {
    void busyUi.run("refreshingCandidates", () => loadCandidates());
  });

  return { loadCandidates, showListView };
}
