/**
 * Side panel candidate review — filtered card list with expandable detail.
 */

import {
  canApprove,
  canApproveWithCriticalOverride,
  canEvaluate,
  canReject,
  isKnownRdeCategory,
  rdeCssClass,
  rdeSeverity,
  statusWithJudgeLabel,
  type CandidateCategory,
} from "./candidate-display.js";
import {
  classifyCandidate,
  isPersonaDump,
  matchesReviewFilter,
  recommendedActionKey,
  reviewClassLabelKey,
  riskHintKey,
  type ReviewFilterId,
} from "./candidate-review-class.js";
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

export type SidepanelCandidateDeps = {
  $: (id: string) => HTMLElement;
  send: (message: BackgroundMessage) => Promise<BackgroundResponse>;
  busyUi: BusyUiController;
  formatBridgeError: (res: Extract<BackgroundResponse, { ok: false }>) => string;
  getStoredEvalLevel: () => number;
};

type CardState = {
  diffLoaded: boolean;
  detail: CandidateDetail | null;
};

export function initSidepanelCandidateUI(deps: SidepanelCandidateDeps): {
  loadCandidates: (preferId?: string) => Promise<void>;
  getActiveFilter: () => ReviewFilterId;
} {
  const { $, send, busyUi, formatBridgeError, getStoredEvalLevel } = deps;

  let activeFilter: ReviewFilterId = "review_required";
  let allCandidates: CandidateSummary[] = [];
  const cardState = new Map<string, CardState>();
  const laterSkipped = new Set<string>();

  function locale(): SupportedLocale {
    return getLocale();
  }

  function setStatus(text: string, isError = false): void {
    const el = $("status-msg");
    el.textContent = text;
    el.className = isError ? "status error" : "status";
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

  function filteredCandidates(): CandidateSummary[] {
    return sortCandidates(allCandidates).filter(
      (c) => !laterSkipped.has(c.id) && matchesReviewFilter(c, activeFilter),
    );
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

  async function fetchDetail(candidateId: string): Promise<CandidateDetail | null> {
    const cached = cardState.get(candidateId)?.detail;
    if (cached) return cached;
    const res = await send({ type: "BRIDGE_GET_CANDIDATE", candidateId });
    if (!res.ok) return null;
    const detail = res.data as CandidateDetail;
    cardState.set(candidateId, { diffLoaded: false, detail });
    return detail;
  }

  async function renderDiffInto(container: HTMLElement, candidateId: string): Promise<void> {
    const state = cardState.get(candidateId);
    if (state?.diffLoaded) return;

    container.textContent = t("status.loading");
    const res = await send({ type: "BRIDGE_DIFF_CANDIDATE", candidateId });
    container.textContent = "";
    if (!res.ok) {
      const p = document.createElement("p");
      p.className = "diff-note";
      p.textContent = formatBridgeError(res);
      container.appendChild(p);
      return;
    }
    const diff = res.data as CandidateDiff;
    if (typeof diff.note === "string" && diff.note) {
      const noteEl = document.createElement("p");
      noteEl.className = "diff-note";
      noteEl.textContent = diff.note;
      container.appendChild(noteEl);
    }
    const addItems = (diff.add ?? diff.proposed_add ?? []) as unknown[];
    for (const item of addItems) {
      const line = document.createElement("div");
      line.className = "diff-add";
      line.textContent = diffLineText(item);
      container.appendChild(line);
    }
    for (const item of (diff.already_present ?? []) as unknown[]) {
      const line = document.createElement("div");
      line.className = "diff-present";
      line.textContent = diffLineText(item);
      container.appendChild(line);
    }
    if (addItems.length === 0 && !(diff.already_present ?? []).length && !diff.note) {
      container.textContent = t("detail.diff_empty");
    }
    cardState.set(candidateId, {
      diffLoaded: true,
      detail: state?.detail ?? null,
    });
  }

  function renderPersonaWarning(parent: HTMLElement, c: CandidateSummary): void {
    const preview = c.content_preview ?? "";
    const section = c.section ?? "";
    if (!isPersonaDump(preview, section)) return;
    const p = document.createElement("p");
    p.className = "persona-warning";
    p.textContent = t("review.persona_dump_warning");
    parent.appendChild(p);
  }

  function renderExpandedBody(
    body: HTMLElement,
    c: CandidateSummary,
    detail: CandidateDetail,
  ): void {
    body.textContent = "";
    renderPersonaWarning(body, c);

    const why = document.createElement("p");
    why.className = "card-why";
    const cls = classifyCandidate(c);
    why.textContent = t(riskHintKey(cls));
    body.appendChild(why);

    const sectionRow = document.createElement("p");
    sectionRow.className = "meta-line";
    sectionRow.textContent = `${t("detail.section")}: ${detail.proposal.section}`;
    body.appendChild(sectionRow);

    const captureLabel = document.createElement("p");
    captureLabel.className = "subheading";
    captureLabel.textContent = t("review.capture_excerpt");
    body.appendChild(captureLabel);
    const capturePre = document.createElement("pre");
    capturePre.className = "content-preview";
    capturePre.textContent = detail.content.slice(0, 1200);
    body.appendChild(capturePre);

    if (detail.proposal.add?.length) {
      const propLabel = document.createElement("p");
      propLabel.className = "subheading";
      propLabel.textContent = t("detail.proposal");
      body.appendChild(propLabel);
      const ul = document.createElement("ul");
      ul.className = "proposal-list";
      for (const item of detail.proposal.add) {
        const li = document.createElement("li");
        li.textContent = typeof item === "string" ? item : String(item);
        ul.appendChild(li);
      }
      body.appendChild(ul);
    }

    const diffLabel = document.createElement("p");
    diffLabel.className = "subheading";
    diffLabel.textContent = t("detail.diff");
    body.appendChild(diffLabel);
    const diffEl = document.createElement("div");
    diffEl.className = "diff-panel";
    diffEl.dataset.candidateId = c.id;
    body.appendChild(diffEl);
    void renderDiffInto(diffEl, c.id);

    if (detail.evaluation?.notes?.length) {
      const notesLabel = document.createElement("p");
      notesLabel.className = "subheading";
      notesLabel.textContent = t("review.classification_reason");
      body.appendChild(notesLabel);
      const notesUl = document.createElement("ul");
      notesUl.className = "eval-notes";
      for (const note of detail.evaluation.notes) {
        const line = formatEvaluationNote(
          typeof note === "string"
            ? note
            : {
                source: note.source,
                key: note.key,
                params: note.params as Record<string, string | number | boolean | null> | undefined,
                text: note.text,
              },
          locale(),
        );
        if (!line) continue;
        const li = document.createElement("li");
        li.textContent = line;
        notesUl.appendChild(li);
      }
      body.appendChild(notesUl);
    }

    const evalLevel = detail.evaluation?.level ?? getStoredEvalLevel();
    const actions = document.createElement("div");
    actions.className = "card-expanded-actions";

    if (canEvaluate(detail.status)) {
      const evalRow = document.createElement("div");
      evalRow.className = "row";
      const levelSelect = document.createElement("select");
      for (const level of [1, 2, 3]) {
        const opt = document.createElement("option");
        opt.value = String(level);
        opt.textContent = t(`candidate.level${level}`);
        levelSelect.appendChild(opt);
      }
      levelSelect.value = String(Math.min(evalLevel, 3));
      const evalBtn = document.createElement("button");
      evalBtn.type = "button";
      evalBtn.className = "btn-primary";
      evalBtn.textContent = t("candidate.evaluate");
      evalBtn.addEventListener("click", () => {
        void runEvaluate(c.id, Number(levelSelect.value) || 1);
      });
      evalRow.appendChild(levelSelect);
      evalRow.appendChild(evalBtn);
      actions.appendChild(evalRow);
    }

    const criticalPanel = document.createElement("div");
    criticalPanel.className = "critical-override-panel";
    criticalPanel.hidden = detail.evaluation?.rde_class !== "Critical Distortion";
    if (!criticalPanel.hidden) {
      const warn = document.createElement("p");
      warn.className = "critical-override-warning";
      warn.textContent = t("detail.critical_override_warning");
      criticalPanel.appendChild(warn);
      const reasonInput = document.createElement("input");
      reasonInput.type = "text";
      reasonInput.placeholder = t("detail.critical_override_reason_placeholder");
      reasonInput.className = "override-reason";
      criticalPanel.appendChild(reasonInput);
      const label = document.createElement("label");
      label.className = "critical-override-label";
      const check = document.createElement("input");
      check.type = "checkbox";
      check.className = "override-check";
      label.appendChild(check);
      const span = document.createElement("span");
      span.textContent = t("detail.critical_override_confirm");
      label.appendChild(span);
      criticalPanel.appendChild(label);
      actions.appendChild(criticalPanel);

      actions.dataset.hasCritical = "1";
    }

    const rejectInput = document.createElement("input");
    rejectInput.type = "text";
    rejectInput.placeholder = t("detail.reject_reason_placeholder");
    rejectInput.className = "reject-reason";
    actions.appendChild(rejectInput);

    const btnRow = document.createElement("div");
    btnRow.className = "row";
    const approveBtn = document.createElement("button");
    approveBtn.type = "button";
    approveBtn.className = "btn-approve";
    approveBtn.textContent = t("candidate.approve");
    approveBtn.disabled =
      busyUi.shouldDisableCandidateActions()
      || !canApproveWithCriticalOverride(
        detail.status,
        (detail.evaluation?.rde_class ?? null) as CandidateCategory | null,
      );
    approveBtn.addEventListener("click", () => {
      void runApprove(c.id, actions);
    });

    const rejectBtn = document.createElement("button");
    rejectBtn.type = "button";
    rejectBtn.className = "btn-reject";
    rejectBtn.textContent = t("candidate.reject");
    rejectBtn.disabled = busyUi.shouldDisableCandidateActions() || !canReject(detail.status);
    rejectBtn.addEventListener("click", () => {
      const reason = (actions.querySelector(".reject-reason") as HTMLInputElement).value.trim();
      void runReject(c.id, reason || undefined);
    });

    btnRow.appendChild(approveBtn);
    btnRow.appendChild(rejectBtn);
    actions.appendChild(btnRow);
    body.appendChild(actions);

    if (activeFilter === "debug") {
      const debugPre = document.createElement("pre");
      debugPre.className = "debug-block";
      debugPre.textContent = [
        `id: ${detail.id}`,
        `rde: ${detail.evaluation?.rde_class ?? "-"}`,
        `status: ${detail.status}`,
        `section: ${detail.proposal.section}`,
      ].join("\n");
      body.appendChild(debugPre);
    }
  }

  async function runEvaluate(candidateId: string, level: number): Promise<void> {
    await busyUi.run("evaluating", async () => {
      setStatus(t("status.loading"));
      const res = await send({ type: "BRIDGE_EVALUATE_CANDIDATE", candidateId, level });
      if (!res.ok) {
        setStatus(formatBridgeError(res), true);
        return;
      }
      cardState.delete(candidateId);
      setStatus(t("status.evaluated", { summary: "" }));
      await loadCandidates(candidateId);
    });
  }

  async function runApprove(candidateId: string, actionsEl: HTMLElement): Promise<void> {
    const critical = actionsEl.dataset.hasCritical === "1";
    const overrideCheck = actionsEl.querySelector(".override-check") as HTMLInputElement | null;
    const overrideReason = actionsEl.querySelector(".override-reason") as HTMLInputElement | null;
    if (critical && overrideCheck && !overrideCheck.checked) {
      setStatus(t("detail.critical_override_required"), true);
      return;
    }
    if (critical && overrideReason && !overrideReason.value.trim()) {
      setStatus(t("detail.critical_override_reason_required"), true);
      return;
    }
    if (critical && !window.confirm(t("detail.critical_override_confirm_dialog"))) return;

    await busyUi.run("approving", async () => {
      const res = await send({
        type: "BRIDGE_APPROVE_CANDIDATE",
        candidateId,
        forceCritical: critical && Boolean(overrideCheck?.checked),
        overrideReason: critical ? overrideReason?.value.trim() : undefined,
      });
      if (!res.ok) {
        setStatus(formatBridgeError(res), true);
        return;
      }
      cardState.delete(candidateId);
      setStatus(t("status.approved", { id: candidateId.slice(0, 8) }));
      await loadCandidates();
    });
  }

  async function runReject(candidateId: string, reason?: string): Promise<void> {
    await busyUi.run("rejecting", async () => {
      const res = await send({
        type: "BRIDGE_REJECT_CANDIDATE",
        candidateId,
        reason,
      });
      if (!res.ok) {
        setStatus(formatBridgeError(res), true);
        return;
      }
      cardState.delete(candidateId);
      setStatus(t("status.rejected", { id: candidateId.slice(0, 8) }));
      await loadCandidates();
    });
  }

  function createCard(c: CandidateSummary, preferOpen: boolean): HTMLElement {
    const cls = classifyCandidate(c);
    const article = document.createElement("article");
    article.className = "review-card";
    article.dataset.candidateId = c.id;

    const badge = document.createElement("span");
    badge.className = `class-badge class-${cls}`;
    badge.textContent = t(reviewClassLabelKey(cls));
    article.appendChild(badge);

    const summary = document.createElement("p");
    summary.className = "card-summary";
    summary.textContent = c.content_preview.slice(0, 160);
    article.appendChild(summary);

    const actionHint = document.createElement("p");
    actionHint.className = "card-action-hint";
    actionHint.textContent = t(recommendedActionKey(cls));
    article.appendChild(actionHint);

    const riskHint = document.createElement("p");
    riskHint.className = "card-risk-hint";
    riskHint.textContent = t(riskHintKey(cls));
    article.appendChild(riskHint);

    if (c.rde_class && isKnownRdeCategory(c.rde_class)) {
      const rde = document.createElement("span");
      rde.className = `rde-badge ${rdeCssClass(c.rde_class)}`;
      rde.textContent = statusWithJudgeLabel(c.status, c.evaluation_status, locale());
      article.appendChild(rde);
    }

    const quickActions = document.createElement("div");
    quickActions.className = "card-quick-actions";
    const laterBtn = document.createElement("button");
    laterBtn.type = "button";
    laterBtn.className = "btn-later";
    laterBtn.textContent = t("review.later");
    laterBtn.addEventListener("click", () => {
      laterSkipped.add(c.id);
      article.remove();
      updateEmptyState();
    });
    quickActions.appendChild(laterBtn);
    article.appendChild(quickActions);

    const details = document.createElement("details");
    details.className = "card-expand";
    const summaryEl = document.createElement("summary");
    summaryEl.textContent = t("review.expand");
    details.appendChild(summaryEl);
    const body = document.createElement("div");
    body.className = "card-expanded-body";
    details.appendChild(body);

    details.addEventListener("toggle", () => {
      if (!details.open) return;
      void fetchDetail(c.id).then((detail) => {
        if (!detail) {
          body.textContent = t("status.loading");
          return;
        }
        renderExpandedBody(body, c, detail);
      });
    });

    if (preferOpen) {
      details.open = true;
      void fetchDetail(c.id).then((detail) => {
        if (detail) renderExpandedBody(body, c, detail);
      });
    }

    article.appendChild(details);
    return article;
  }

  function updateEmptyState(): void {
    const empty = $("empty-msg");
    const container = $("candidate-cards");
    const visible = container.querySelectorAll(".review-card").length;
    if (visible === 0) {
      empty.hidden = false;
      empty.textContent = t("review.empty_filter");
    } else {
      empty.hidden = true;
      empty.textContent = "";
    }
  }

  function renderCards(preferId?: string): void {
    const container = $("candidate-cards");
    container.textContent = "";
    const items = filteredCandidates();
    if (items.length === 0) {
      updateEmptyState();
      return;
    }
    $("empty-msg").hidden = true;
    for (const c of items) {
      container.appendChild(createCard(c, c.id === preferId));
    }
  }

  async function loadCandidates(preferId?: string): Promise<void> {
    const res = await send({ type: "BRIDGE_LIST_CANDIDATES" });
    if (!res.ok) {
      setStatus(localizeError(res.error), true);
      return;
    }
    allCandidates = res.data as CandidateSummary[];
    cardState.clear();
    renderCards(preferId);
    setStatus("");
  }

  ($("filter-select") as HTMLSelectElement).addEventListener("change", () => {
    activeFilter = ($("filter-select") as HTMLSelectElement).value as ReviewFilterId;
    laterSkipped.clear();
    renderCards();
  });

  $("btn-refresh-candidates").addEventListener("click", () => {
    void busyUi.run("refreshingCandidates", () => loadCandidates());
  });

  return {
    loadCandidates,
    getActiveFilter: () => activeFilter,
  };
}
