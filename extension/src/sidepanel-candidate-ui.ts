/**
 * Side panel candidate review — filtered card list with expandable detail.
 */

import {
  canEvaluate,
  canReject,
  categoryLabel,
  isKnownRdeCategory,
  rdeCssClass,
  rdeSeverity,
  type CandidateCategory,
} from "./candidate-display.js";
import {
  approveUnavailableMessage,
  canApproveCandidate,
  effectiveCandidateStatus,
  getApproveAvailability,
  readApproveContextFromActions,
  readApproveContextFromButton,
  syncSummaryFromDetail,
  type ApproveAvailability,
} from "./approve-availability.js";
import {
  classifyCandidate,
  isPersonaDump,
  matchesReviewFilter,
  recommendedActionKeyForCandidate,
  reviewClassLabelKey,
  riskHintKeyForCandidate,
  type ReviewFilterId,
} from "./candidate-review-class.js";
import {
  isAutoMergeSupported,
  isBlockedMergeSection,
  isCriticalSection,
  requiresExplicitContextConfirmation,
  requiresForceCriticalMerge,
} from "./merge-policy.js";
import { loadConfig } from "./config.js";
import {
  applyDisabledWithCursorHint,
  type BusyUiController,
} from "./busy-ui.js";
import { getLocale, localizeError, t } from "./i18n.js";
import { formatEvaluationNote } from "./rde-notes.js";
import {
  captureExcerptForReview,
  captureExcerptLineCount,
  detectImportantTermsLargeCapture,
  detectCaptureScopeMismatch,
  filterStoredContextForSection,
} from "./capture-excerpt.js";
import {
  importantTermsCardSummary,
  isListDiffSection,
  listDiffFromBridgeDiff,
  listDiffFromProposal,
  proposalItemsForListSection,
} from "./list-diff.js";
import { countImportantTermsInCapture } from "./clipboard-preview.js";
import {
  type CandidateActionState,
  type CardActionRecord,
  isBusyActionState,
  isResolvedActionState,
} from "./candidate-action-state.js";
import {
  CURRENT_REVIEW_SESSION_KEY,
  filterCandidatesForReviewSession,
  loadCurrentReviewSession,
  type CandidateReviewSession,
} from "./review-session.js";
import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateDetail,
  CandidateDiff,
  CandidateLineage,
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
  focusCandidate: (candidateId: string) => Promise<void>;
  getActiveFilter: () => ReviewFilterId;
  applyShowDebugUi: () => Promise<void>;
} {
  const { $, send, busyUi, formatBridgeError, getStoredEvalLevel } = deps;

  let activeFilter: ReviewFilterId = "review_required";
  let showDebugUi = true;
  let allCandidates: CandidateSummary[] = [];
  const cardState = new Map<string, CardState>();
  const laterSkipped = new Set<string>();
  const expandedCandidateIds = new Set<string>();
  let currentReviewSession: CandidateReviewSession | null = null;
  let loadGeneration = 0;
  const cardActions = new Map<string, CardActionRecord>();
  const expandedApproveSync = new Map<string, () => void>();

  function isApproveConfirmationInput(input: HTMLInputElement): boolean {
    return (
      input.classList.contains("explicit-confirm-reason")
      || input.classList.contains("explicit-confirm-check")
      || input.classList.contains("override-reason")
      || input.classList.contains("override-check")
    );
  }

  function getCardAction(candidateId: string): CandidateActionState {
    return cardActions.get(candidateId)?.state ?? "idle";
  }

  function setCardAction(
    candidateId: string,
    state: CandidateActionState,
    options?: { rawError?: string },
  ): void {
    const prev = cardActions.get(candidateId);
    cardActions.set(candidateId, {
      state,
      rawError:
        options?.rawError
        ?? (state === "error" ? prev?.rawError : undefined),
    });
    applyCardActionUi(candidateId);
  }

  function applyCardActionUi(candidateId: string): void {
    const card = document.querySelector<HTMLElement>(
      `[data-candidate-id="${candidateId}"]`,
    );
    if (!card) return;

    const record = cardActions.get(candidateId);
    const actionState = record?.state ?? "idle";
    const busy = isBusyActionState(actionState);
    const c = allCandidates.find((item) => item.id === candidateId);
    const rawDetail = cardState.get(candidateId)?.detail;
    const detail = rawDetail === null ? undefined : rawDetail;
    if (c && detail) syncSummaryFromDetail(c, detail);

    const statusBadge = card.querySelector<HTMLElement>(".card-action-status");
    if (isResolvedActionState(actionState)) {
      if (!statusBadge) {
        const el = document.createElement("p");
        el.className = "card-action-status";
        card.querySelector(".card-quick-actions")?.before(el);
      }
      const badge = card.querySelector<HTMLElement>(".card-action-status");
      if (badge) {
        badge.textContent =
          actionState === "approved"
            ? t("review.status.approved")
            : t("review.status.rejected");
      }
    } else if (statusBadge) {
      statusBadge.remove();
    }

    const debugRaw = card.querySelector<HTMLElement>(".debug-raw-error");
    if (showDebugUi && record?.rawError && actionState === "error") {
      if (!debugRaw) {
        const pre = document.createElement("pre");
        pre.className = "debug-block debug-raw-error";
        card.appendChild(pre);
      }
      const pre = card.querySelector<HTMLElement>(".debug-raw-error");
      if (pre) {
        pre.textContent = `${t("debug.last_error_raw")}\n${record.rawError}`;
      }
    } else if (debugRaw) {
      debugRaw.remove();
    }

    card.querySelectorAll<HTMLButtonElement>("button").forEach((btn) => {
      const idleLabel = btn.dataset.idleLabel;
      if (busy) {
        applyDisabledWithCursorHint(btn, true, "busy");
        if (actionState === "evaluating" && btn.classList.contains("btn-primary")) {
          btn.textContent = t("busy.evaluating");
        } else if (actionState === "approving" && btn.classList.contains("btn-approve")) {
          btn.textContent = t("busy.approving");
        } else if (actionState === "rejecting" && btn.classList.contains("btn-reject")) {
          btn.textContent = t("busy.rejecting");
        } else if (actionState === "deferring" && btn.classList.contains("btn-later")) {
          btn.textContent = t("busy.processing");
        }
        return;
      }
      if (actionState === "approved" && btn.classList.contains("btn-approve")) {
        btn.textContent = t("review.status.approved");
        applyDisabledWithCursorHint(btn, true, null);
        return;
      }
      if (idleLabel) btn.textContent = idleLabel;
      if (!c) {
        applyDisabledWithCursorHint(btn, false, null);
        return;
      }
      if (btn.classList.contains("btn-approve")) {
        const compact = btn.classList.contains("btn-compact");
        if (!compact) {
          const sync = expandedApproveSync.get(candidateId);
          if (sync) {
            sync();
            return;
          }
        }
        const actionsEl = compact
          ? null
          : expandedActionsForApproveButton(btn, candidateId);
        const opts = approveOptionsFor(
          c,
          detail ?? undefined,
          actionsEl,
          compact,
          btn,
        );
        const avail = getApproveAvailability(c, detail ?? undefined, opts);
        const canUse =
          actionState !== "approved" && canApproveCandidate(c, detail ?? undefined, opts);
        applyDisabledWithCursorHint(btn, !canUse, canUse ? null : "unavailable");
        if (!busy && actionState !== "approved") {
          const label = t(avail.labelKey);
          btn.dataset.idleLabel = label;
          if (actionState === "idle") btn.textContent = label;
          btn.title = avail.reasonKey ? t(avail.reasonKey) : "";
        }
        if (!compact) {
          const hint = actionsEl?.querySelector<HTMLElement>(".approve-blocked-hint");
          if (hint) {
            if (!canUse) {
              hint.hidden = false;
              hint.textContent = approveUnavailableMessage(
                c,
                detail ?? undefined,
                avail,
                locale(),
                t,
              );
            } else {
              hint.hidden = true;
              hint.textContent = "";
            }
          }
        }
      } else if (btn.classList.contains("btn-reject")) {
        applyDisabledWithCursorHint(
          btn,
          !canReject(c.status) || actionState === "approved",
          null,
        );
      } else if (btn.classList.contains("btn-later")) {
        applyDisabledWithCursorHint(btn, actionState === "approved", null);
      } else if (btn.classList.contains("btn-primary")) {
        applyDisabledWithCursorHint(btn, false, null);
      } else {
        applyDisabledWithCursorHint(btn, false, null);
      }
    });

    card.querySelectorAll<HTMLSelectElement>("select").forEach((sel) => {
      sel.disabled = busy || actionState === "approved";
    });
    card.querySelectorAll<HTMLInputElement>("input").forEach((input) => {
      if (isApproveConfirmationInput(input)) {
        input.disabled = actionState === "approved";
        return;
      }
      input.disabled = busy || actionState === "approved";
    });
  }

  busyUi.setOnStateChange(() => {
    if (busyUi.shouldDisableCandidateActions()) {
      $("candidate-cards")
        .querySelectorAll<HTMLButtonElement>("button")
        .forEach((btn) => {
          if (!btn.closest("[data-candidate-id]")) return;
        });
    }
  });

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

  function formatSessionTimestamp(iso: string): string {
    return iso.length >= 19 ? iso.slice(0, 19) : iso;
  }

  function updateReviewSessionHeader(): void {
    const existing = document.getElementById("review-session-banner");
    if (!currentReviewSession) {
      existing?.remove();
      return;
    }
    const banner =
      existing ??
      (() => {
        const el = document.createElement("div");
        el.id = "review-session-banner";
        el.className = "review-session-banner";
        $("candidate-cards").before(el);
        return el;
      })();
    banner.replaceChildren();
    const text = document.createElement("p");
    text.className = "review-session-text";
    const raw = currentReviewSession.rawCaptureText.trim();
    const lines = raw ? captureExcerptLineCount(raw) : 0;
    text.textContent = t("review.session_header", {
      source: t(`review.session.source.${currentReviewSession.source}`),
      capturedAt: formatSessionTimestamp(currentReviewSession.capturedAt),
      lines: String(lines),
      chars: String(raw.length),
    });
    banner.appendChild(text);
    if (raw) {
      const preview = document.createElement("pre");
      preview.className = "review-session-excerpt";
      preview.textContent = raw.slice(0, 240);
      banner.appendChild(preview);
    }
  }

  function cardCapturePreview(c: CandidateSummary, detail?: CandidateDetail): string {
    if (c.section === "important_terms") {
      const summary = importantTermsCardSummary(c);
      if (summary) return summary.slice(0, 200);
    }
    if (detail && currentReviewSession) {
      return captureExcerptForReview(detail, currentReviewSession).slice(0, 160);
    }
    if (
      currentReviewSession
      && currentReviewSession.candidateIds.includes(c.id)
      && currentReviewSession.rawCaptureText.trim()
    ) {
      return currentReviewSession.rawCaptureText.trim().slice(0, 160);
    }
    const withSummary = c as CandidateSummary & { display_summary?: string | null };
    return (withSummary.display_summary?.trim() || c.content_preview).slice(0, 160);
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

  async function fetchDetail(
    candidateId: string,
    options?: { refresh?: boolean },
  ): Promise<CandidateDetail | null> {
    if (options?.refresh) {
      cardState.delete(candidateId);
    }
    const cached = cardState.get(candidateId)?.detail;
    if (cached) return cached;
    const res = await send({ type: "BRIDGE_GET_CANDIDATE", candidateId });
    if (!res.ok) return null;
    const detail = res.data as CandidateDetail;
    cardState.set(candidateId, { diffLoaded: false, detail });
    return detail;
  }

  function approveOptionsFor(
    c: CandidateSummary,
    detail: CandidateDetail | undefined,
    actionsEl: HTMLElement | null | undefined,
    compact: boolean,
    approveBtn?: HTMLButtonElement | null,
  ) {
    const contextFromDom =
      !compact && actionsEl
        ? readApproveContextFromActions(actionsEl)
        : approveBtn && !compact
          ? readApproveContextFromButton(approveBtn)
          : readApproveContextFromActions(actionsEl);
    return {
      compact,
      cardActionState: getCardAction(c.id),
      ...contextFromDom,
    };
  }

  function expandedActionsForApproveButton(
    btn: HTMLButtonElement,
    candidateId: string,
  ): HTMLElement | null {
    return (
      btn.closest<HTMLElement>(".card-expanded-actions")
      ?? document
        .querySelector<HTMLElement>(`[data-candidate-id="${candidateId}"]`)
        ?.querySelector<HTMLElement>(".card-expanded-actions")
      ?? null
    );
  }

  function bindApproveInputRefresh(
    input: HTMLInputElement | null | undefined,
    refresh: () => void,
  ): void {
    if (!input) return;
    const schedule = () => queueMicrotask(refresh);
    input.addEventListener("input", schedule);
    input.addEventListener("change", schedule);
    if (input.type !== "checkbox") {
      input.addEventListener("compositionend", schedule);
    }
  }

  /** Recompute expanded approve button when explicit or override inputs change. */
  function bindApproveInputsRefresh(
    actions: HTMLElement,
    sync: () => void,
  ): void {
    bindApproveInputRefresh(
      actions.querySelector<HTMLInputElement>(".explicit-confirm-reason"),
      sync,
    );
    bindApproveInputRefresh(
      actions.querySelector<HTMLInputElement>(".explicit-confirm-check"),
      sync,
    );
    bindApproveInputRefresh(
      actions.querySelector<HTMLInputElement>(".override-reason"),
      sync,
    );
    bindApproveInputRefresh(
      actions.querySelector<HTMLInputElement>(".override-check"),
      sync,
    );
    Array.from(
      actions.querySelectorAll<HTMLLabelElement>(
        ".explicit-confirm-label, .critical-override-label",
      ),
    ).forEach((label) => {
      label.addEventListener("click", () => queueMicrotask(sync));
    });
  }

  function refreshExpandedApproveUi(candidateId: string): void {
    const sync = expandedApproveSync.get(candidateId);
    if (sync) {
      sync();
      return;
    }
    applyCardActionUi(candidateId);
  }

  function resolveActionsEl(
    candidateId: string,
    actionsEl: HTMLElement,
    compact: boolean,
    approveBtn?: HTMLButtonElement | null,
  ): HTMLElement {
    if (!compact) {
      return (
        approveBtn?.closest<HTMLElement>(".card-expanded-actions")
        ?? actionsEl.closest<HTMLElement>(".card-expanded-actions")
        ?? expandedActionsForApproveButton(
          approveBtn ?? (actionsEl.querySelector(".btn-approve") as HTMLButtonElement),
          candidateId,
        )
        ?? actionsEl
      );
    }
    return actionsEl;
  }

  function handleApproveClick(
    c: CandidateSummary,
    actionsEl: HTMLElement,
    compact: boolean,
  ): void {
    const summary = allCandidates.find((item) => item.id === c.id);
    if (!summary) {
      setStatus(t("review.approve_not_found"), true);
      return;
    }
    const detail = cardState.get(c.id)?.detail ?? undefined;
    syncSummaryFromDetail(summary, detail);
    const resolvedActions = resolveActionsEl(c.id, actionsEl, compact);
    const approveBtn = resolvedActions.querySelector<HTMLButtonElement>(".btn-approve");
    const opts = approveOptionsFor(
      summary,
      detail,
      resolvedActions,
      compact,
      approveBtn,
    );
    const avail = getApproveAvailability(summary, detail, opts);
    if (avail.kind === "needs_evaluation") {
      setStatus(t("review.approve_requires_evaluation"), true);
      return;
    }
    if (!canApproveCandidate(summary, detail, opts)) {
      const msg = approveUnavailableMessage(summary, detail, avail, locale(), t);
      setStatus(msg, true);
      if (!compact) {
        const hint = resolvedActions.querySelector<HTMLElement>(".approve-blocked-hint");
        if (hint) {
          hint.hidden = false;
          hint.textContent = msg;
        }
      }
      return;
    }
    void runApproveEvaluated(c.id, resolvedActions);
  }

  function applyApproveButtonState(
    btn: HTMLButtonElement,
    c: CandidateSummary,
    detail: CandidateDetail | null | undefined,
    compact: boolean,
    actionsEl?: HTMLElement | null,
    hintEl?: HTMLElement | null,
  ): ApproveAvailability {
    const resolvedDetail = detail === null ? undefined : detail;
    const resolvedActions =
      actionsEl
      ?? (compact ? null : expandedActionsForApproveButton(btn, c.id));
    const opts = approveOptionsFor(
      c,
      resolvedDetail,
      resolvedActions,
      compact,
      btn,
    );
    const avail = getApproveAvailability(c, resolvedDetail, opts);
    const label = t(avail.labelKey);
    btn.textContent = label;
    btn.dataset.idleLabel = label;
    btn.title = avail.reasonKey ? t(avail.reasonKey) : "";
    const canUse = canApproveCandidate(c, resolvedDetail, opts);
    applyDisabledWithCursorHint(btn, !canUse, canUse ? null : "unavailable");
    if (hintEl) {
      if (!canUse) {
        const msg = approveUnavailableMessage(c, resolvedDetail, avail, locale(), t);
        hintEl.hidden = false;
        hintEl.textContent = msg;
        btn.title = msg;
      } else {
        hintEl.hidden = true;
        hintEl.textContent = "";
        btn.title = avail.reasonKey ? t(avail.reasonKey) : "";
      }
    }
    return avail;
  }

  function lineageSourceLabel(kind: string | null | undefined): string {
    if (kind === "selection") return t("review.lineage.source_selection");
    if (kind === "clipboard") return t("review.lineage.source_clipboard");
    if (kind === "page") return t("review.lineage.source_page");
    return kind ?? "—";
  }

  function lineageDecisionLabel(
    decision: CandidateLineage["decision"],
  ): string {
    const key = `review.lineage.decision_${decision}` as const;
    const label = t(key);
    return label === key ? decision : label;
  }

  function renderCandidateLineage(host: HTMLElement, lineage: CandidateLineage): void {
    host.replaceChildren();
    const dl = document.createElement("dl");
    dl.className = "lineage-summary";
    const addRow = (labelKey: string, value: string): void => {
      const dt = document.createElement("dt");
      dt.textContent = t(labelKey);
      const dd = document.createElement("dd");
      dd.textContent = value;
      dl.append(dt, dd);
    };
    addRow(
      "review.lineage.capture",
      `${lineageSourceLabel(lineage.source_kind)} · ${lineage.captured_at.slice(0, 19)}`,
    );
    addRow("review.lineage.candidate", lineage.candidate_id.slice(0, 12));
    const loc = locale();
    let evalText = t("review.lineage.not_evaluated");
    if (lineage.rde_class && isKnownRdeCategory(lineage.rde_class)) {
      evalText = `${t("review.lineage.evaluated")} · ${categoryLabel(lineage.rde_class, loc)}`;
    } else if (lineage.evaluation_status === "judge_failed") {
      evalText = t("review.lineage.judge_failed");
    } else if (lineage.status === "evaluated") {
      evalText = t("review.lineage.evaluated");
    }
    addRow("review.lineage.evaluation", evalText);
    addRow("review.lineage.decision", lineageDecisionLabel(lineage.decision));
    if (lineage.context_path) {
      addRow("review.lineage.target", lineage.context_path);
    }
    if (lineage.source_candidate_id) {
      addRow(
        "review.lineage.revised_from",
        lineage.source_candidate_id.slice(0, 12),
      );
    }
    host.appendChild(dl);
    if (lineage.source_url) {
      const url = document.createElement("p");
      url.className = "lineage-url meta-line";
      url.textContent = lineage.source_url;
      host.appendChild(url);
    }
  }

  function renderListDiffLines(
    container: HTMLElement,
    listDiff: ReturnType<typeof listDiffFromBridgeDiff>,
  ): boolean {
    if (!listDiff) return false;

    if (listDiff.added.length > 0) {
      const label = document.createElement("p");
      label.className = "diff-section-label";
      label.textContent = t("review.list_diff_added");
      container.appendChild(label);
      for (const name of listDiff.added) {
        const line = document.createElement("div");
        line.className = "diff-add";
        line.textContent = `- ${name}`;
        container.appendChild(line);
      }
    }

    if (listDiff.removed.length > 0) {
      const label = document.createElement("p");
      label.className = "diff-section-label";
      label.textContent = t("review.list_diff_removed");
      container.appendChild(label);
      for (const name of listDiff.removed) {
        const line = document.createElement("div");
        line.className = "diff-remove";
        line.textContent = `- ${name}`;
        container.appendChild(line);
      }
    }

    const unchangedCount = listDiff.unchangedCount ?? listDiff.unchanged.length;
    if (unchangedCount > 0) {
      const details = document.createElement("details");
      details.className = "list-diff-unchanged";
      const summary = document.createElement("summary");
      summary.textContent = t("review.list_diff_unchanged_count", {
        count: String(unchangedCount),
      });
      details.appendChild(summary);
      const list = document.createElement("div");
      list.className = "diff-present-list";
      for (const name of listDiff.unchanged) {
        const line = document.createElement("div");
        line.className = "diff-present";
        line.textContent = `- ${name}`;
        list.appendChild(line);
      }
      details.appendChild(list);
      container.appendChild(details);
    }

    return (
      listDiff.added.length > 0
      || listDiff.removed.length > 0
      || unchangedCount > 0
    );
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
    const section =
      (typeof diff.section === "string" ? diff.section : null)
      ?? allCandidates.find((c) => c.id === candidateId)?.section
      ?? "";
    const listDiff = isListDiffSection(section)
      ? listDiffFromBridgeDiff(diff)
      : null;

    if (listDiff && renderListDiffLines(container, listDiff)) {
      cardState.set(candidateId, {
        diffLoaded: true,
        detail: state?.detail ?? null,
      });
      return;
    }

    if (typeof diff.note === "string" && diff.note) {
      const noteEl = document.createElement("p");
      noteEl.className = "diff-note";
      noteEl.textContent = diff.note;
      container.appendChild(noteEl);
    }
    const addItems = (diff.add ?? diff.proposed_add ?? []) as unknown[];
    const presentAll = (diff.already_present ?? []) as unknown[];
    const present = filterStoredContextForSection(presentAll, section);

    if (present.length > 0) {
      const savedLabel = document.createElement("p");
      savedLabel.className = "diff-section-label";
      savedLabel.textContent = t("review.saved_context");
      container.appendChild(savedLabel);
      for (const item of present) {
        const line = document.createElement("div");
        line.className = "diff-present";
        line.textContent = diffLineText(item);
        container.appendChild(line);
      }
    }

    if (addItems.length > 0) {
      const proposedLabel = document.createElement("p");
      proposedLabel.className = "diff-section-label";
      proposedLabel.textContent = t("review.proposed_changes");
      container.appendChild(proposedLabel);
    }

    for (const item of addItems) {
      const line = document.createElement("div");
      line.className = "diff-add";
      line.textContent = diffLineText(item);
      container.appendChild(line);
    }
    if (addItems.length === 0 && present.length === 0 && !diff.note) {
      container.textContent = t("detail.diff_empty");
    }
    cardState.set(candidateId, {
      diffLoaded: true,
      detail: state?.detail ?? null,
    });
  }

  function renderProposalSection(
    parent: HTMLElement,
    detail: CandidateDetail,
    listDiffOverride?: import("./list-diff.js").ListDiff | null,
  ): void {
    const adds = detail.proposal.add ?? [];
    const section = detail.proposal.section ?? "";
    const listDiff = listDiffOverride ?? listDiffFromProposal(detail);
    const items = proposalItemsForListSection(detail);

    if (adds.length === 0 && items.length === 0 && !listDiff?.unchanged.length) {
      return;
    }

    const propLabel = document.createElement("p");
    propLabel.className = "subheading";
    propLabel.textContent = t("detail.proposal");
    parent.appendChild(propLabel);

    if (listDiff && isListDiffSection(section)) {
      if (listDiff.added.length > 0) {
        const addLabel = document.createElement("p");
        addLabel.className = "diff-section-label";
        addLabel.textContent = t("review.list_diff_added");
        parent.appendChild(addLabel);
        const ul = document.createElement("ul");
        ul.className = "proposal-list";
        for (const name of listDiff.added) {
          const li = document.createElement("li");
          li.textContent = `important_terms[] · ${name}`;
          ul.appendChild(li);
        }
        parent.appendChild(ul);
      }
      if (listDiff.removed.length > 0) {
        const remLabel = document.createElement("p");
        remLabel.className = "diff-section-label";
        remLabel.textContent = t("review.list_diff_removed");
        parent.appendChild(remLabel);
        const ul = document.createElement("ul");
        ul.className = "proposal-list proposal-removed";
        for (const name of listDiff.removed) {
          const li = document.createElement("li");
          li.textContent = `important_terms[] · ${name}`;
          ul.appendChild(li);
        }
        parent.appendChild(ul);
      }
      const unchangedCount = listDiff.unchanged.length;
      if (unchangedCount > 0) {
        const details = document.createElement("details");
        details.className = "list-diff-unchanged";
        const summary = document.createElement("summary");
        summary.textContent = t("review.list_diff_unchanged_proposal", {
          count: String(unchangedCount),
        });
        details.appendChild(summary);
        const ul = document.createElement("ul");
        ul.className = "proposal-list";
        for (const name of listDiff.unchanged) {
          const li = document.createElement("li");
          li.textContent = name;
          ul.appendChild(li);
        }
        details.appendChild(ul);
        parent.appendChild(details);
      }
      return;
    }

    const ul = document.createElement("ul");
    ul.className = "proposal-list";
    for (const item of adds) {
      const li = document.createElement("li");
      li.textContent = typeof item === "string" ? item : String(item);
      ul.appendChild(li);
    }
    for (const item of items) {
      const li = document.createElement("li");
      const name = typeof item.name === "string" ? item.name : "";
      const path = typeof item.yaml_path === "string" ? item.yaml_path : item.path;
      const summary = typeof item.summary === "string" ? item.summary : "";
      li.textContent = [path, name, summary].filter(Boolean).join(" · ");
      ul.appendChild(li);
    }
    parent.appendChild(ul);
  }

  function renderCaptureScopeWarnings(
    parent: HTMLElement,
    detail: CandidateDetail,
    excerpt: string,
  ): void {
    const messages: string[] = [];
    if (detectCaptureScopeMismatch(detail, excerpt)) {
      messages.push(t("review.capture_scope_mismatch"));
    }
    const metaWarnings = detail.capture_meta?.capture_warnings ?? [];
    if (metaWarnings.includes("full_persona_document_detected")) {
      messages.push(t("review.full_persona_capture_warning"));
    }
    if (metaWarnings.includes("clipboard_many_important_terms")) {
      messages.push(t("review.clipboard_many_important_terms"));
    }
    if (
      (detail.proposal.section ?? "") === "important_terms"
      && detectImportantTermsLargeCapture(excerpt)
    ) {
      const count = countImportantTermsInCapture(excerpt);
      messages.push(t("review.important_terms_large_capture", { count: String(count) }));
    }
    for (const msg of messages) {
      const p = document.createElement("p");
      p.className = "persona-warning";
      p.textContent = msg;
      parent.appendChild(p);
    }
  }

  function renderPersonaWarning(
    parent: HTMLElement,
    c: CandidateSummary,
    detail?: CandidateDetail,
  ): void {
    const preview = detail && currentReviewSession
      ? captureExcerptForReview(detail, currentReviewSession)
      : (c.content_preview ?? "");
    const section = c.section ?? detail?.proposal.section ?? "";
    if (!isPersonaDump(preview, section)) return;
    const p = document.createElement("p");
    p.className = "persona-warning";
    p.textContent = t("review.persona_dump_warning");
    parent.appendChild(p);
  }

  function renderStoragePolicy(parent: HTMLElement, detail: CandidateDetail): void {
    const sp = detail.storage_policy;
    if (!sp) return;
    const container = document.createElement("div");
    container.className = "storage-policy-panel";
    const heading = document.createElement("p");
    heading.className = "subheading";
    heading.textContent = t("detail.storage_policy");
    container.appendChild(heading);
    const dl = document.createElement("dl");
    dl.className = "storage-policy-list";
    const addRow = (labelKey: string, value: string): void => {
      const dt = document.createElement("dt");
      dt.textContent = t(labelKey);
      const dd = document.createElement("dd");
      dd.textContent = value;
      dl.append(dt, dd);
    };
    addRow("detail.target_path", sp.target_path);
    addRow("detail.storage_kind", t(`detail.storage_kind.${sp.storage_kind}`));
    addRow("detail.prompt_export", t(`detail.prompt_export.${sp.prompt_export}`));
    addRow("detail.sensitivity", t(`detail.sensitivity.${sp.sensitivity}`));
    if (detail.parent_capture_id) {
      addRow("detail.parent_capture", detail.parent_capture_id.slice(0, 12));
    }
    container.appendChild(dl);
    const note = document.createElement("p");
    note.className = "card-why";
    note.textContent = t("review.risk.persona_ir_split");
    container.appendChild(note);
    parent.appendChild(container);
  }

  function renderExpandedBody(
    body: HTMLElement,
    c: CandidateSummary,
    detail: CandidateDetail,
  ): void {
    body.textContent = "";
    const prev = cardState.get(c.id);
    cardState.set(c.id, { diffLoaded: prev?.diffLoaded ?? false, detail });
    const summary = allCandidates.find((item) => item.id === c.id);
    if (summary) syncSummaryFromDetail(summary, detail);
    renderPersonaWarning(body, c, detail);

    const captureExcerpt = captureExcerptForReview(detail, currentReviewSession);
    renderCaptureScopeWarnings(body, detail, captureExcerpt);

    // #124: Show storage policy for IR-split candidates.
    if (detail.storage_policy) {
      renderStoragePolicy(body, detail);
    }

    const why = document.createElement("p");
    why.className = "card-why";
    const cls = classifyCandidate(c);
    why.textContent = t(riskHintKeyForCandidate(c));
    body.appendChild(why);

    const sectionRow = document.createElement("p");
    sectionRow.className = "meta-line";
    sectionRow.textContent = `${t("detail.section")}: ${detail.proposal.section}`;
    body.appendChild(sectionRow);

    const lineageBlock = document.createElement("details");
    lineageBlock.className = "lineage-panel";
    lineageBlock.open = true;
    const lineageSummary = document.createElement("summary");
    lineageSummary.textContent = t("review.lineage");
    lineageBlock.appendChild(lineageSummary);
    const lineageBody = document.createElement("div");
    lineageBody.className = "lineage-body";
    lineageBody.textContent = t("review.lineage.loading");
    lineageBlock.appendChild(lineageBody);
    body.appendChild(lineageBlock);
    void send({ type: "BRIDGE_GET_CANDIDATE_LINEAGE", candidateId: c.id }).then((res) => {
      if (!res.ok) {
        lineageBody.textContent = t("review.lineage.unavailable");
        return;
      }
      renderCandidateLineage(lineageBody, res.data as CandidateLineage);
    });

    const captureLabel = document.createElement("p");
    captureLabel.className = "subheading";
    captureLabel.textContent = t("review.capture_excerpt");
    body.appendChild(captureLabel);
    const capturePre = document.createElement("pre");
    capturePre.className = "content-preview";
    capturePre.textContent = captureExcerpt;
    body.appendChild(capturePre);

    const proposalHost = document.createElement("div");
    proposalHost.className = "proposal-host";
    body.appendChild(proposalHost);

    const diffLabel = document.createElement("p");
    diffLabel.className = "subheading";
    diffLabel.textContent = t("detail.diff");
    body.appendChild(diffLabel);
    const diffEl = document.createElement("div");
    diffEl.className = "diff-panel";
    diffEl.dataset.candidateId = c.id;
    body.appendChild(diffEl);

    void (async () => {
      const section = detail.proposal.section ?? "";
      let listDiffForProposal: import("./list-diff.js").ListDiff | null = null;
      if (isListDiffSection(section)) {
        const res = await send({ type: "BRIDGE_DIFF_CANDIDATE", candidateId: c.id });
        if (res.ok) {
          listDiffForProposal = listDiffFromBridgeDiff(res.data as CandidateDiff);
        }
      }
      renderProposalSection(proposalHost, detail, listDiffForProposal);
      await renderDiffInto(diffEl, c.id);
    })();

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
      evalBtn.dataset.idleLabel = t("candidate.evaluate");
      evalBtn.addEventListener("click", () => {
        void runEvaluate(c.id, Number(levelSelect.value) || 1);
      });
      evalRow.appendChild(levelSelect);
      evalRow.appendChild(evalBtn);
      actions.appendChild(evalRow);
    }

    const mergeSection = detail.proposal.section;
    const blockedSection = isBlockedMergeSection(mergeSection);
    const mergeUnsupported = !isAutoMergeSupported(mergeSection);
    const needsForceMerge = requiresForceCriticalMerge(mergeSection);
    const isCriticalRde = detail.evaluation?.rde_class === "Critical Distortion";

    if (blockedSection) {
      const blockedWarn = document.createElement("p");
      blockedWarn.className = "merge-blocked-warning";
      blockedWarn.textContent = t("detail.merge_section_blocked", { section: mergeSection });
      actions.appendChild(blockedWarn);
    } else if (mergeUnsupported) {
      const unsupportedWarn = document.createElement("p");
      unsupportedWarn.className = "merge-blocked-warning";
      unsupportedWarn.textContent = t("error.merge_section_unsupported", {
        section: mergeSection,
      });
      actions.appendChild(unsupportedWarn);
    }

    const needsExplicitConfirm = requiresExplicitContextConfirmation(mergeSection);
    if (needsExplicitConfirm) {
      const explicitPanel = document.createElement("div");
      explicitPanel.className = "explicit-confirm-panel";
      const warn = document.createElement("p");
      warn.className = "explicit-confirm-warning";
      warn.textContent = t("detail.force_critical_section_warning", {
        section: mergeSection,
      });
      explicitPanel.appendChild(warn);
      const adoptReason = document.createElement("input");
      adoptReason.type = "text";
      adoptReason.placeholder = t("detail.explicit_confirm_reason_placeholder");
      adoptReason.className = "explicit-confirm-reason";
      explicitPanel.appendChild(adoptReason);
      const label = document.createElement("label");
      label.className = "explicit-confirm-label";
      const check = document.createElement("input");
      check.type = "checkbox";
      check.className = "explicit-confirm-check";
      label.appendChild(check);
      const span = document.createElement("span");
      span.textContent = t("detail.force_critical_section_confirm", {
        section: mergeSection,
      });
      label.appendChild(span);
      explicitPanel.appendChild(label);
      actions.appendChild(explicitPanel);
      actions.dataset.requiresExplicitConfirmation = "1";
    }

    const needsSectionOverride =
      needsForceMerge && isCriticalSection(mergeSection);
    const criticalPanel = document.createElement("div");
    criticalPanel.className = "critical-override-panel";
    criticalPanel.hidden = !isCriticalRde && !needsSectionOverride;
    if (!criticalPanel.hidden) {
      const warn = document.createElement("p");
      warn.className = "critical-override-warning";
      warn.textContent = isCriticalRde
        ? t("detail.critical_override_warning")
        : t("detail.force_critical_section_warning", { section: mergeSection });
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
      span.textContent = isCriticalRde
        ? t("detail.critical_override_confirm")
        : t("detail.force_critical_section_confirm", { section: mergeSection });
      label.appendChild(span);
      criticalPanel.appendChild(label);
      actions.appendChild(criticalPanel);

      if (isCriticalRde) actions.dataset.hasCriticalRde = "1";
      if (needsSectionOverride) actions.dataset.hasCriticalSection = "1";
    }

    const approveHint = document.createElement("p");
    approveHint.className = "approve-blocked-hint";
    approveHint.hidden = true;
    approveHint.setAttribute("role", "status");
    actions.appendChild(approveHint);

    const btnRow = document.createElement("div");
    btnRow.className = "row";
    const approveBtn = document.createElement("button");
    approveBtn.type = "button";
    approveBtn.className = "btn-approve";

    const rejectBtn = document.createElement("button");
    rejectBtn.type = "button";
    rejectBtn.className = "btn-reject";
    rejectBtn.textContent = t("candidate.reject");
    rejectBtn.disabled =
      isBusyActionState(getCardAction(c.id)) || !canReject(detail.status);
    rejectBtn.dataset.idleLabel = t("candidate.reject");
    rejectBtn.addEventListener("click", () => {
      const reason = (actions.querySelector(".reject-reason") as HTMLInputElement).value.trim();
      void runReject(c.id, reason || undefined);
    });

    btnRow.appendChild(approveBtn);
    btnRow.appendChild(rejectBtn);
    actions.appendChild(btnRow);

    const rejectInput = document.createElement("input");
    rejectInput.type = "text";
    rejectInput.placeholder = t("detail.reject_reason_placeholder");
    rejectInput.className = "reject-reason";
    actions.appendChild(rejectInput);

    const syncExpandedApprove = (): void => {
      const summary = allCandidates.find((item) => item.id === c.id);
      const liveDetail = cardState.get(c.id)?.detail ?? detail;
      if (!summary) return;
      syncSummaryFromDetail(summary, liveDetail);
      const actionState = getCardAction(c.id);
      const busyAction = isBusyActionState(actionState);
      const opts = approveOptionsFor(summary, liveDetail, actions, false);
      const avail = getApproveAvailability(summary, liveDetail, opts);
      const canUse =
        !busyAction
        && actionState !== "approved"
        && canApproveCandidate(summary, liveDetail, opts);
      const label = t(avail.labelKey);
      approveBtn.dataset.idleLabel = label;
      if (actionState === "idle") approveBtn.textContent = label;
      applyDisabledWithCursorHint(
        approveBtn,
        !canUse,
        busyAction ? "busy" : canUse ? null : "unavailable",
      );
      if (!canUse) {
        const msg = approveUnavailableMessage(summary, liveDetail, avail, locale(), t);
        approveHint.hidden = false;
        approveHint.textContent = msg;
        approveBtn.title = msg;
      } else {
        approveHint.hidden = true;
        approveHint.textContent = "";
        approveBtn.title = "";
      }
    };

    expandedApproveSync.set(c.id, syncExpandedApprove);
    approveBtn.addEventListener("click", () => {
      handleApproveClick(c, actions, false);
    });
    body.appendChild(actions);
    bindApproveInputsRefresh(actions, syncExpandedApprove);
    syncExpandedApprove();

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

  async function reloadCandidateCard(candidateId: string): Promise<void> {
    const [res, session] = await Promise.all([
      send({ type: "BRIDGE_LIST_CANDIDATES" }),
      loadCurrentReviewSession(),
    ]);
    if (!res.ok) {
      setStatus(localizeError(res.error), true);
      return;
    }
    currentReviewSession = session;
    allCandidates = filterCandidatesForReviewSession(
      res.data as CandidateSummary[],
      session,
    );
    cardState.delete(candidateId);
    expandedApproveSync.delete(candidateId);
    expandedCandidateIds.clear();
    expandedCandidateIds.add(candidateId);

    const c = allCandidates.find((item) => item.id === candidateId);
    const container = $("candidate-cards");
    const existing = container.querySelector(
      `[data-candidate-id="${candidateId}"]`,
    );

    if (c && matchesReviewFilter(c, activeFilter)) {
      const newCard = createCard(c, true);
      existing?.replaceWith(newCard);
      $("empty-msg").hidden = true;
    } else {
      existing?.remove();
      updateEmptyState();
    }
  }

  async function runEvaluate(candidateId: string, level: number): Promise<void> {
    expandedCandidateIds.add(candidateId);
    setCardAction(candidateId, "evaluating");
    setStatus(t("busy.evaluating"));
    const res = await send({ type: "BRIDGE_EVALUATE_CANDIDATE", candidateId, level });
    if (!res.ok) {
      setCardAction(candidateId, "error", { rawError: res.error });
      setStatus(formatBridgeError(res), true);
      setCardAction(candidateId, "idle");
      return;
    }
    const evaluated = res.data as CandidateDetail;
    const item = allCandidates.find((entry) => entry.id === candidateId);
    if (item) syncSummaryFromDetail(item, evaluated);
    cardState.set(candidateId, { diffLoaded: false, detail: evaluated });
    setCardAction(candidateId, "idle");
    setStatus(t("status.evaluated", { summary: "" }));
    await reloadCandidateCard(candidateId);
  }

  async function runApproveEvaluated(
    candidateId: string,
    actionsEl: HTMLElement,
  ): Promise<void> {
    expandedCandidateIds.add(candidateId);
    const summary = allCandidates.find((item) => item.id === candidateId);
    if (!summary) {
      setStatus(t("review.approve_not_found"), true);
      return;
    }
    const rawDetail = cardState.get(candidateId)?.detail;
    const detail = rawDetail === null ? undefined : rawDetail;
    syncSummaryFromDetail(summary, detail);
    if (effectiveCandidateStatus(summary, detail) === "pending") {
      setStatus(t("review.evaluate_before_approve_done"), true);
      return;
    }
    const approveOpts = approveOptionsFor(summary, detail, actionsEl, false);
    const avail = getApproveAvailability(summary, detail, approveOpts);
    if (!canApproveCandidate(summary, detail, approveOpts)) {
      if (avail.reasonKey) setStatus(t(avail.reasonKey), true);
      return;
    }

    const section = detail?.proposal.section ?? summary.section ?? "";
    const needsRdeOverride = actionsEl.dataset.hasCriticalRde === "1";
    const needsSectionOverride = actionsEl.dataset.hasCriticalSection === "1";
    const needsOverride = needsRdeOverride || needsSectionOverride;
    const overrideReason = actionsEl.querySelector(".override-reason") as HTMLInputElement | null;
    if (needsOverride && !window.confirm(t("detail.critical_override_confirm_dialog"))) {
      setStatus(t("detail.critical_override_required"), true);
      return;
    }

    const explicitReason = actionsEl.querySelector(
      ".explicit-confirm-reason",
    ) as HTMLInputElement | null;
    const explicitCheck = actionsEl.querySelector(
      ".explicit-confirm-check",
    ) as HTMLInputElement | null;
    const explicitConfirmation =
      actionsEl.dataset.requiresExplicitConfirmation === "1"
      && explicitCheck?.checked
      && explicitReason?.value.trim()
        ? {
            section,
            checked: true as const,
            reason: explicitReason.value.trim(),
            confirmedAt: new Date().toISOString(),
          }
        : undefined;

    setCardAction(candidateId, "approving");
    const res = await send({
      type: "BRIDGE_APPROVE_CANDIDATE",
      candidateId,
      forceCritical: needsOverride,
      overrideReason: needsOverride ? overrideReason?.value.trim() : undefined,
      explicitConfirmation,
    });
    if (!res.ok) {
      setCardAction(candidateId, "error", { rawError: res.error });
      setStatus(formatBridgeError(res), true);
      setCardAction(candidateId, "idle");
      await reloadCandidateCard(candidateId);
      return;
    }
    cardState.delete(candidateId);
    const item = allCandidates.find((c) => c.id === candidateId);
    if (item) {
      item.status = "approved";
    }
    setCardAction(candidateId, "approved");
    setStatus(t("status.approved", { id: candidateId.slice(0, 8) }));
    await reloadCandidateCard(candidateId);
  }

  async function runReject(candidateId: string, reason?: string): Promise<void> {
    setCardAction(candidateId, "rejecting");
    const res = await send({
      type: "BRIDGE_REJECT_CANDIDATE",
      candidateId,
      reason,
    });
    if (!res.ok) {
      setCardAction(candidateId, "error", { rawError: res.error });
      setStatus(formatBridgeError(res), true);
      setCardAction(candidateId, "idle");
      await reloadCandidateCard(candidateId);
      return;
    }
    cardState.delete(candidateId);
    const item = allCandidates.find((c) => c.id === candidateId);
    if (item) {
      item.status = "rejected";
    }
    setCardAction(candidateId, "rejected");
    setStatus(t("status.rejected", { id: candidateId.slice(0, 8) }));
    await reloadCandidateCard(candidateId);
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
    summary.textContent = cardCapturePreview(c);
    article.appendChild(summary);

    const actionHint = document.createElement("p");
    actionHint.className = "card-action-hint";
    actionHint.textContent = t(recommendedActionKeyForCandidate(c));
    article.appendChild(actionHint);

    const riskHint = document.createElement("p");
    riskHint.className = "card-risk-hint";
    riskHint.textContent = t(riskHintKeyForCandidate(c));
    article.appendChild(riskHint);

    if (c.rde_class && isKnownRdeCategory(c.rde_class)) {
      const rde = document.createElement("span");
      rde.className = `rde-badge ${rdeCssClass(c.rde_class)}`;
      rde.textContent = categoryLabel(c.rde_class, locale());
      article.appendChild(rde);
    }

    const quickActions = document.createElement("div");
    quickActions.className = "card-quick-actions";

    const mergeSection = c.section ?? "";
    const detailForCompact = cardState.get(c.id)?.detail;
    const compactSection = detailForCompact?.proposal?.section ?? mergeSection;
    const compactCriticalRde =
      detailForCompact?.evaluation?.rde_class === "Critical Distortion"
      || c.rde_class === "Critical Distortion";
    const compactNeedsOverrideUi =
      compactCriticalRde
      || (requiresForceCriticalMerge(compactSection) && isCriticalSection(compactSection));
    const hideCompactApprove =
      requiresExplicitContextConfirmation(compactSection) || compactNeedsOverrideUi;
    if (!hideCompactApprove) {
      const approveBtn = document.createElement("button");
      approveBtn.type = "button";
      approveBtn.className = "btn-approve btn-compact";
      approveBtn.textContent = t("candidate.approve");
      approveBtn.dataset.idleLabel = t("candidate.approve");
      applyApproveButtonState(approveBtn, c, cardState.get(c.id)?.detail, true);
      approveBtn.addEventListener("click", () => {
        handleApproveClick(c, document.createElement("div"), true);
      });
      quickActions.appendChild(approveBtn);
    }

    const rejectBtn = document.createElement("button");
    rejectBtn.type = "button";
    rejectBtn.className = "btn-reject btn-compact";
    rejectBtn.textContent = t("candidate.reject");
    rejectBtn.dataset.idleLabel = t("candidate.reject");
    rejectBtn.disabled =
      isBusyActionState(getCardAction(c.id)) || !canReject(c.status);
    rejectBtn.addEventListener("click", () => {
      void runReject(c.id);
    });

    const laterBtn = document.createElement("button");
    laterBtn.type = "button";
    laterBtn.className = "btn-later";
    laterBtn.textContent = t("review.later");
    laterBtn.addEventListener("click", () => {
      laterSkipped.add(c.id);
      article.remove();
      updateEmptyState();
    });
    quickActions.appendChild(rejectBtn);
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
      if (details.open) {
        expandedCandidateIds.add(c.id);
        void fetchDetail(c.id).then((detail) => {
          if (!detail) {
            body.textContent = t("status.loading");
            return;
          }
          renderExpandedBody(body, c, detail);
          refreshExpandedApproveUi(c.id);
        });
      } else {
        expandedCandidateIds.delete(c.id);
      }
    });

    article.appendChild(details);

    const shouldOpen = preferOpen || expandedCandidateIds.has(c.id);
    if (shouldOpen) {
      details.open = true;
      void fetchDetail(c.id, { refresh: true }).then((detail) => {
        if (detail) {
          renderExpandedBody(body, c, detail);
          refreshExpandedApproveUi(c.id);
        }
      });
    }

    applyCardActionUi(c.id);
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
    if (preferId) {
      expandedCandidateIds.clear();
      expandedCandidateIds.add(preferId);
    }
    const container = $("candidate-cards");
    container.textContent = "";
    updateReviewSessionHeader();
    const items = filteredCandidates();
    if (items.length === 0) {
      updateEmptyState();
      return;
    }
    $("empty-msg").hidden = true;
    for (const c of items) {
      const preferOpen =
        c.id === preferId || expandedCandidateIds.has(c.id);
      container.appendChild(createCard(c, preferOpen));
    }
  }

  async function repairSessionRawCaptureIfNeeded(): Promise<void> {
    if (!currentReviewSession) return;
    if (currentReviewSession.rawCaptureText.trim()) return;
    const focusId =
      currentReviewSession.candidateIds[0] ?? currentReviewSession.captureId;
    if (!focusId) return;
    const res = await send({ type: "BRIDGE_GET_CANDIDATE", candidateId: focusId });
    if (!res.ok) return;
    const detail = res.data as CandidateDetail;
    const excerpt =
      detail.source_excerpt?.trim() || detail.raw_capture?.trim() || "";
    if (!excerpt) return;
    currentReviewSession = {
      ...currentReviewSession,
      rawCaptureText: excerpt,
    };
    await chrome.storage.local.set({
      [CURRENT_REVIEW_SESSION_KEY]: currentReviewSession,
    });
  }

  async function loadCandidates(preferId?: string): Promise<void> {
    const generation = ++loadGeneration;
    const [res, session] = await Promise.all([
      send({ type: "BRIDGE_LIST_CANDIDATES" }),
      loadCurrentReviewSession(),
    ]);
    if (!res.ok) {
      setStatus(localizeError(res.error), true);
      return;
    }
    if (generation !== loadGeneration) {
      return;
    }
    currentReviewSession = session;
    await repairSessionRawCaptureIfNeeded();
    const bridgeList = res.data as CandidateSummary[];
    allCandidates = filterCandidatesForReviewSession(bridgeList, session);
    cardState.clear();
    renderCards(preferId);
    setStatus("");
    if (preferId) {
      document
        .querySelector(`[data-candidate-id="${preferId}"]`)
        ?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }

  async function focusCandidate(candidateId: string): Promise<void> {
    expandedCandidateIds.clear();
    expandedCandidateIds.add(candidateId);
    await loadCandidates(candidateId);
  }

  async function applyShowDebugUiSetting(): Promise<void> {
    const config = await loadConfig();
    showDebugUi = config.showDebugUi;
    const debugOption = document.getElementById("filter-option-debug");
    if (debugOption instanceof HTMLOptionElement) {
      debugOption.hidden = !showDebugUi;
    }
    if (!showDebugUi && activeFilter === "debug") {
      activeFilter = "review_required";
      ($("filter-select") as HTMLSelectElement).value = activeFilter;
      renderCards();
    }
  }

  ($("filter-select") as HTMLSelectElement).addEventListener("change", () => {
    activeFilter = ($("filter-select") as HTMLSelectElement).value as ReviewFilterId;
    laterSkipped.clear();
    renderCards();
  });

  $("btn-refresh-candidates").addEventListener("click", () => {
    void busyUi.run("refreshingCandidates", () => loadCandidates());
  });

  void applyShowDebugUiSetting();

  return {
    loadCandidates,
    focusCandidate,
    getActiveFilter: () => activeFilter,
    applyShowDebugUi: applyShowDebugUiSetting,
  };
}
