/**
 * Side panel candidate review — filtered card list with expandable detail.
 */

import {
  canApproveWithCriticalOverride,
  canEvaluate,
  canReject,
  categoryLabel,
  isKnownRdeCategory,
  rdeCssClass,
  rdeSeverity,
  type CandidateCategory,
} from "./candidate-display.js";
import {
  classifyCandidate,
  isPersonaDump,
  matchesReviewFilter,
  recommendedActionKeyForCandidate,
  reviewClassLabelKey,
  riskHintKeyForCandidate,
  shouldBlockBulkApprove,
  type ReviewFilterId,
} from "./candidate-review-class.js";
import {
  isAutoMergeSupported,
  isBlockedMergeSection,
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
    const detail = cardState.get(candidateId)?.detail;

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
        const canApprove =
          actionState !== "approved"
          && (detail
            ? canInitiateApproveFromDetail(c, detail)
            : canQuickApprove(c));
        applyDisabledWithCursorHint(btn, !canApprove, canApprove ? null : "unavailable");
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

  /** Compact card approve — persona / sensitive_review must open details first. */
  function canQuickApprove(c: CandidateSummary): boolean {
    if (!isAutoMergeSupported(c.section ?? "")) return false;
    if (shouldBlockBulkApprove(c)) return false;
    return canInitiateApprove(c);
  }

  /** Approve from expanded panel (pending → auto-evaluate on click, then approve). */
  function canInitiateApprove(c: CandidateSummary): boolean {
    if (c.status === "approved" || c.status === "rejected") return false;
    if (requiresForceCriticalMerge(c.section ?? "")) return false;
    if (c.status === "pending") return true;
    if (c.rde_class === "Critical Distortion") return false;
    return canApproveWithCriticalOverride(
      c.status,
      (c.rde_class ?? null) as CandidateCategory | null,
    );
  }

  function canInitiateApproveFromDetail(
    c: CandidateSummary,
    detail: CandidateDetail,
  ): boolean {
    if (detail.status === "approved" || detail.status === "rejected") return false;
    if (requiresForceCriticalMerge(detail.proposal.section)) return false;
    if (detail.status === "pending") return true;
    const category = (detail.evaluation?.rde_class ?? null) as CandidateCategory | null;
    return canApproveWithCriticalOverride(detail.status, category);
  }

  function approveButtonTitle(c: CandidateSummary, compact: boolean): string {
    if (compact && shouldBlockBulkApprove(c)) return t("review.approve_blocked_hint");
    if (c.status === "pending") return t("review.approve_will_evaluate_hint");
    return "";
  }

  async function ensureEvaluatedForApprove(
    candidateId: string,
  ): Promise<CandidateSummary | null> {
    let summary = allCandidates.find((item) => item.id === candidateId);
    if (!summary) return null;
    if (summary.status !== "pending") return summary;

    const level = Math.min(getStoredEvalLevel(), 3);
    await runEvaluate(candidateId, level);
    summary = allCandidates.find((item) => item.id === candidateId);
    return summary ?? null;
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

  function renderExpandedBody(
    body: HTMLElement,
    c: CandidateSummary,
    detail: CandidateDetail,
  ): void {
    body.textContent = "";
    renderPersonaWarning(body, c, detail);

    const captureExcerpt = captureExcerptForReview(detail, currentReviewSession);
    renderCaptureScopeWarnings(body, detail, captureExcerpt);

    const why = document.createElement("p");
    why.className = "card-why";
    const cls = classifyCandidate(c);
    why.textContent = t(riskHintKeyForCandidate(c));
    body.appendChild(why);

    const sectionRow = document.createElement("p");
    sectionRow.className = "meta-line";
    sectionRow.textContent = `${t("detail.section")}: ${detail.proposal.section}`;
    body.appendChild(sectionRow);

    const lineageRow = document.createElement("p");
    lineageRow.className = "meta-line lineage-line";
    lineageRow.textContent = `${t("review.lineage")}: ${detail.id.slice(0, 12)} · ${c.captured_at.slice(0, 19)}`;
    body.appendChild(lineageRow);

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

    const criticalPanel = document.createElement("div");
    criticalPanel.className = "critical-override-panel";
    criticalPanel.hidden = !isCriticalRde && !needsForceMerge;
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
      if (needsForceMerge) actions.dataset.hasCriticalSection = "1";
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
      isBusyActionState(getCardAction(c.id))
      || blockedSection
      || mergeUnsupported
      || !canInitiateApproveFromDetail(c, detail);
    approveBtn.dataset.idleLabel = t("candidate.approve");
    approveBtn.title = approveButtonTitle(c, false);
    approveBtn.addEventListener("click", () => {
      void runApprove(c.id, actions);
    });

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
    cardState.delete(candidateId);
    setCardAction(candidateId, "idle");
    setStatus(t("status.evaluated", { summary: "" }));
    await reloadCandidateCard(candidateId);
  }

  async function runApprove(candidateId: string, actionsEl: HTMLElement): Promise<void> {
    expandedCandidateIds.add(candidateId);
    const summary = await ensureEvaluatedForApprove(candidateId);
    if (!summary) {
      setStatus(t("review.approve_not_found"), true);
      return;
    }
    if (summary.status === "pending") {
      setStatus(t("review.approve_evaluate_failed"), true);
      return;
    }
    const category = (summary.rde_class ?? null) as CandidateCategory | null;
    if (!canApproveWithCriticalOverride(summary.status, category)) {
      if (category === "Critical Distortion") {
        setStatus(t("detail.critical_override_required"), true);
      } else {
        setStatus(t("review.approve_blocked_after_eval"), true);
      }
      return;
    }

    const needsOverride =
      actionsEl.dataset.hasCriticalRde === "1"
      || actionsEl.dataset.hasCriticalSection === "1";
    const overrideCheck = actionsEl.querySelector(".override-check") as HTMLInputElement | null;
    const overrideReason = actionsEl.querySelector(".override-reason") as HTMLInputElement | null;
    if (needsOverride && overrideCheck && !overrideCheck.checked) {
      setStatus(t("detail.critical_override_required"), true);
      return;
    }
    if (needsOverride && overrideReason && !overrideReason.value.trim()) {
      setStatus(t("detail.critical_override_reason_required"), true);
      return;
    }
    if (needsOverride && !window.confirm(t("detail.critical_override_confirm_dialog"))) return;

    setCardAction(candidateId, "approving");
    const res = await send({
      type: "BRIDGE_APPROVE_CANDIDATE",
      candidateId,
      forceCritical: needsOverride && Boolean(overrideCheck?.checked),
      overrideReason: needsOverride ? overrideReason?.value.trim() : undefined,
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

    const approveBtn = document.createElement("button");
    approveBtn.type = "button";
    approveBtn.className = "btn-approve btn-compact";
    approveBtn.textContent = t("candidate.approve");
    approveBtn.dataset.idleLabel = t("candidate.approve");
    approveBtn.disabled =
      isBusyActionState(getCardAction(c.id)) || !canQuickApprove(c);
    approveBtn.title = approveButtonTitle(c, true);
    approveBtn.addEventListener("click", () => {
      void runApprove(c.id, document.createElement("div"));
    });

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
    quickActions.appendChild(approveBtn);
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
        if (detail) renderExpandedBody(body, c, detail);
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
