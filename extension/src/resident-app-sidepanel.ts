import { readAppContract } from "./app-bootstrap-reader.js";
import { readCandidateDiff } from "./candidate-diff-reader.js";
import { readCandidateLineage } from "./candidate-lineage-reader.js";
import { t } from "./i18n.js";
import { loadCurrentReviewSession } from "./review-session.js";
import {
  readCandidateDetailScreenState,
  readCandidateQueueScreenState,
  readDaemonPanelScreenState,
  readHomeScreenState,
} from "./screen-state-reader.js";
import { peekCandidatesFocusId } from "./sidepanel-client.js";
import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateDiff,
  CandidateDetailScreenState,
  CandidateLineage,
  CandidateQueueScreenState,
  DaemonPanelScreenState,
  HomeScreenState,
  ResidentAppContract,
} from "./types.js";
import { listDiffFromBridgeDiff } from "./list-diff.js";

export type ResidentAppSidepanelDeps = {
  $: (id: string) => HTMLElement;
  send: (message: BackgroundMessage) => Promise<BackgroundResponse>;
  formatBridgeError: (res: Extract<BackgroundResponse, { ok: false }>) => string;
  loadCandidateQueue: () => Promise<void>;
  focusCandidate: (candidateId: string) => Promise<void>;
};

type ActiveReviewState = {
  sessionExists: boolean;
  candidateId: string | null;
  source: string | null;
  count: number;
};

type SummaryEntry = {
  key: string;
  value: string;
};

type ButtonOptions = {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  title?: string;
  activeCandidateId?: string | null;
};

function localizeReviewSessionSource(source: string | null): string {
  if (!source) return "—";
  const key = `review.session.source.${source}`;
  const translated = t(key);
  return translated === key ? source : translated;
}

const RESIDENT_APP_DISPLAY_VALUE_KEYS: Record<string, string> = {
  pending: "resident_app.value.pending",
  evaluated: "resident_app.value.evaluated",
  approved: "resident_app.value.approved",
  rejected: "resident_app.value.rejected",
  stopped: "resident_app.value.stopped",
  review_required: "resident_app.value.review_required",
  manual_review_required: "resident_app.value.manual_review_required",
  present_review_required: "resident_app.value.present_review_required",
  create: "resident_app.value.create",
  missing: "resident_app.value.missing",
  runtime_init: "resident_app.value.runtime_init",
  runtime_root: "resident_app.value.runtime_root",
  pid_file: "resident_app.value.pid_file",
  lock_file: "resident_app.value.lock_file",
  selection: "resident_app.value.selection",
  clipboard: "resident_app.value.clipboard",
  page: "resident_app.value.page",
  manual: "resident_app.value.manual",
  "knowledge.concepts": "resident_app.value.knowledge_concepts",
  important_terms: "resident_app.value.important_terms",
  add: "resident_app.value.add",
  list_add: "resident_app.value.list_add",
  available: "resident_app.value.available",
  unavailable: "resident_app.value.unavailable",
};

const RESIDENT_APP_DISPLAY_FIELD_KEYS: Record<string, string> = {
  id: "resident_app.field.id",
  kind: "resident_app.field.kind",
  operation_id: "resident_app.field.operation_id",
  plan_fingerprint: "resident_app.field.plan_fingerprint",
  review_required: "resident_app.field.review_required",
  operator_confirmation_signal: "resident_app.field.operator_confirmation_signal",
  metadata_path: "resident_app.field.metadata_path",
  preview_hash: "resident_app.field.preview_hash",
  allowed_targets: "resident_app.field.allowed_targets",
  decision_policy: "resident_app.field.decision_policy",
  manual_review_required: "resident_app.field.manual_review_required",
  section: "resident_app.field.section",
  operation: "resident_app.field.operation",
  level: "resident_app.field.level",
  status: "resident_app.field.status",
  source: "resident_app.field.source",
  source_type: "resident_app.field.source_type",
  capture_id: "resident_app.field.capture_id",
  decision: "resident_app.field.decision",
  rde_class: "resident_app.field.rde_class",
  events: "resident_app.field.events",
  path_role: "resident_app.field.path_role",
  path: "resident_app.field.path",
  reason: "resident_app.field.reason",
  artifact_kind: "resident_app.field.artifact_kind",
  diagnostic_status: "resident_app.field.diagnostic_status",
  recommendation: "resident_app.field.recommendation",
  target: "resident_app.field.target",
  repairable: "resident_app.field.repairable",
  evaluation_level: "resident_app.field.evaluation_level",
  added_count: "resident_app.field.added_count",
  already_present_count: "resident_app.field.already_present_count",
  list_operation: "resident_app.field.list_operation",
  evaluate: "resident_app.field.action_evaluate",
  approve: "resident_app.field.action_approve",
  reject: "resident_app.field.action_reject",
  revise: "resident_app.field.action_revise",
};

const RESIDENT_APP_DISPLAY_PHRASE_KEYS: Record<string, string> = {
  "Initialize runtime metadata before daemon start": "resident_app.phrase.runtime_init_before_start",
  "missing directory may be created with explicit apply intent": "resident_app.phrase.reason_missing_directory_apply",
  "artifact is present; ownership and liveness are not proven by preview diagnostics":
    "resident_app.phrase.reason_artifact_present_review",
  "artifact is present": "resident_app.phrase.reason_artifact_present_short",
  "Inspect missing runtime directories before any control action.":
    "resident_app.phrase.reason_inspect_missing_runtime",
  "Review ambiguous daemon artifacts before mutation or control.":
    "resident_app.phrase.reason_review_ambiguous_artifacts",
  "Runtime initialization preview currently requires manual review.":
    "resident_app.phrase.reason_runtime_init_manual_review",
  "Reviewed stale-file cleanup candidates are available.":
    "resident_app.phrase.reason_reviewed_cleanup_available",
  "Missing runtime directories can be reviewed for explicit repair.":
    "resident_app.phrase.reason_missing_runtime_repair",
  "Observe bounded readiness signals for the running local daemon.":
    "resident_app.phrase.reason_observe_bounded_readiness",
  "Current daemon state is stable; refresh status when needed.":
    "resident_app.phrase.reason_state_stable_refresh",
};

function clearChildren(node: HTMLElement): void {
  node.replaceChildren();
}

function stringifyValue(value: unknown): string {
  if (typeof value === "boolean") {
    return value ? t("resident_app.value.true") : t("resident_app.value.false");
  }
  if (value == null) return "—";
  if (Array.isArray(value)) {
    return value.map((item) => stringifyValue(item)).join(", ") || "—";
  }
  const stringValue = String(value);
  const phraseKey = RESIDENT_APP_DISPLAY_PHRASE_KEYS[stringValue];
  if (phraseKey) return t(phraseKey);
  const valueKey = RESIDENT_APP_DISPLAY_VALUE_KEYS[stringValue];
  if (valueKey) return t(valueKey);
  return stringValue;
}

function localizeFieldKey(key: string): string {
  const translationKey = RESIDENT_APP_DISPLAY_FIELD_KEYS[key];
  if (translationKey) return t(translationKey);
  return key.replaceAll("_", " ");
}

function prioritizeActiveReviewItem<T>(
  items: T[],
  activeCandidateId: string | null,
  pickId: (item: T) => string | null,
): T[] {
  if (!activeCandidateId) return items;
  const active: T[] = [];
  const rest: T[] = [];
  for (const item of items) {
    if (pickId(item) === activeCandidateId) {
      active.push(item);
    } else {
      rest.push(item);
    }
  }
  return [...active, ...rest];
}

function renderSummaryEntryList(container: HTMLElement, entries: SummaryEntry[]): void {
  clearChildren(container);
  for (const entry of entries) {
    const row = document.createElement("li");
    row.textContent = `${entry.key}: ${entry.value}`;
    container.appendChild(row);
  }
}

function renderPlainTextList(container: HTMLElement, values: string[]): void {
  clearChildren(container);
  for (const value of values) {
    const row = document.createElement("li");
    row.textContent = value;
    container.appendChild(row);
  }
  container.hidden = values.length === 0;
}

function renderKeyValueRecord(
  container: HTMLElement,
  payload: Record<string, unknown>,
  options?: { emptyHidden?: boolean },
): void {
  clearChildren(container);
  const keys = Object.keys(payload);
  if (keys.length === 0) {
    container.hidden = options?.emptyHidden ?? true;
    return;
  }
  for (const [key, value] of Object.entries(payload)) {
    const row = document.createElement("li");
    row.textContent = `${localizeFieldKey(key)}: ${stringifyValue(value)}`;
    container.appendChild(row);
  }
  container.hidden = false;
}

export function initResidentAppSidepanel(deps: ResidentAppSidepanelDeps): {
  refresh: () => Promise<void>;
  showDaemonPanel: () => Promise<void>;
  showCandidateQueue: () => Promise<void>;
  handleCandidatesChanged: (candidateId: string | null) => Promise<void>;
} {
  const { $, send, formatBridgeError, loadCandidateQueue, focusCandidate } = deps;
  const panel = $("resident-app-panel");
  const meta = $("resident-app-meta");
  const status = $("resident-app-status");
  const activeReview = $("resident-app-active-review");
  const cards = $("resident-app-summary-cards");
  const reviewItems = $("resident-app-review-items");
  const daemonActions = $("resident-app-daemon-actions");
  const quickLinks = $("resident-app-quick-links");
  const daemonPanel = $("resident-app-daemon-panel");
  const daemonSummary = $("resident-app-daemon-summary");
  const daemonRuntime = $("resident-app-daemon-runtime");
  const daemonCleanup = $("resident-app-daemon-cleanup");
  const daemonRepair = $("resident-app-daemon-repair");
  const queuePanel = $("resident-app-queue-panel");
  const queueSummary = $("resident-app-queue-summary");
  const queueOpenActiveReviewButton = $("resident-app-queue-open-active-review") as HTMLButtonElement;
  const queueSections = $("resident-app-queue-sections");
  const queueItems = $("resident-app-queue-items");
  const detailPanel = $("resident-app-detail-panel");
  const detailSummary = $("resident-app-detail-summary");
  const detailActions = $("resident-app-detail-actions");
  const detailActionHints = $("resident-app-detail-action-hints");
  const detailProposal = $("resident-app-detail-proposal");
  const detailEvaluation = $("resident-app-detail-evaluation");
  const detailLineage = $("resident-app-detail-lineage");
  const detailContent = $("resident-app-detail-content");
  const detailDiff = $("resident-app-detail-diff");
  const detailReviewButton = $("resident-app-detail-open-review");
  const detailQueueButton = $("resident-app-detail-back-queue");
  const detailActiveReviewButton = $("resident-app-detail-back-active-review") as HTMLButtonElement;
  let activeReviewState: ActiveReviewState = {
    sessionExists: false,
    candidateId: null,
    source: null,
    count: 0,
  };
  let lastHomeState: HomeScreenState | null = null;
  let lastQueueState: CandidateQueueScreenState | null = null;
  let lastDetailState: CandidateDetailScreenState | null = null;
  let lastDetailCandidateId: string | null = null;

  function renderContract(contract: ResidentAppContract): void {
    meta.textContent = t("resident_app.meta", {
      version: contract.contract_version,
      entrypoint: contract.preferred_entrypoint,
    });
  }

  function formatDetailUnavailable(error: unknown): string {
    return typeof error === "object" && error !== null && "error" in error
      ? formatBridgeError(error as Extract<BackgroundResponse, { ok: false }>)
      : `${t("resident_app.detail_unavailable")} ${String(error)}`;
  }

  async function fallbackToQueueAfterDetailFailure(error: unknown): Promise<void> {
    lastDetailState = null;
    lastDetailCandidateId = null;
    detailPanel.hidden = true;
    status.textContent = t("resident_app.detail_fallback_queue", {
      reason: formatDetailUnavailable(error),
    });
    try {
      const queueState = await readCandidateQueueScreenState(send);
      renderQueuePanelState(queueState);
    } catch (queueError) {
      status.textContent =
        typeof queueError === "object" && queueError !== null && "error" in queueError
          ? formatBridgeError(queueError as Extract<BackgroundResponse, { ok: false }>)
          : `${t("resident_app.queue_unavailable")} ${String(queueError)}`;
    }
  }

  function styleActiveCandidateButton(button: HTMLButtonElement, candidateId: string): void {
    const isActive = activeReviewState.candidateId === candidateId;
    button.classList.toggle("resident-app-link-button-active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  }

  function createResidentActionButton(options: ButtonOptions): HTMLButtonElement {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "resident-app-link-button";
    button.textContent = options.label;
    if (options.activeCandidateId) {
      styleActiveCandidateButton(button, options.activeCandidateId);
    }
    if (options.title) {
      button.title = options.title;
      button.setAttribute("aria-label", options.title);
    }
    if (options.disabled) {
      button.disabled = true;
    } else if (options.onClick) {
      button.addEventListener("click", options.onClick);
    }
    return button;
  }

  function appendResidentActionRow(container: HTMLElement, options: ButtonOptions): void {
    const row = document.createElement("li");
    row.appendChild(createResidentActionButton(options));
    container.appendChild(row);
  }

  function renderActiveReviewSummary(): void {
    if (!activeReviewState.sessionExists) {
      activeReview.textContent = t("resident_app.active.none");
      return;
    }
    activeReview.textContent = t("resident_app.active.current", {
      candidateId: activeReviewState.candidateId ?? "—",
      source: localizeReviewSessionSource(activeReviewState.source),
      count: String(activeReviewState.count),
    });
  }

  function activeReviewButtonReason(currentCandidateId?: string): string {
    if (!activeReviewState.candidateId) {
      return t("resident_app.active_button.unavailable");
    }
    if (currentCandidateId && activeReviewState.candidateId === currentCandidateId) {
      return t("resident_app.active_button.current", {
        candidateId: currentCandidateId,
      });
    }
    return t("resident_app.active_button.available", {
      candidateId: activeReviewState.candidateId,
    });
  }

  async function syncActiveReviewState(nextCandidateId?: string): Promise<void> {
    const [session, focusId] = await Promise.all([
      loadCurrentReviewSession(),
      peekCandidatesFocusId(),
    ]);
    if (!session) {
      activeReviewState = {
        sessionExists: false,
        candidateId: null,
        source: null,
        count: 0,
      };
      renderActiveReviewSummary();
      return;
    }
    activeReviewState = {
      sessionExists: true,
      candidateId: nextCandidateId ?? focusId ?? session.candidateIds[0] ?? null,
      source: session.source,
      count: session.candidateIds.length,
    };
    renderActiveReviewSummary();
  }

  function buildHomeSummaryCards(state: HomeScreenState): Array<{ key: string; value: unknown }> {
    const summaryCards = [...state.summary_cards];
    if (activeReviewState.sessionExists) {
      summaryCards.push(
        { key: "active_review_source", value: activeReviewState.source ?? "—" },
        { key: "active_review_count", value: activeReviewState.count },
        {
          key: "active_review_presence",
          value:
            activeReviewState.candidateId
            && state.top_review_items.some((item) => item.candidate_id === activeReviewState.candidateId)
              ? t("resident_app.summary.active_review_present")
              : t("resident_app.summary.active_review_missing"),
        },
      );
    }
    return summaryCards;
  }

  function renderCards(state: HomeScreenState): void {
    clearChildren(cards);
    for (const card of buildHomeSummaryCards(state)) {
      const item = document.createElement("li");
      item.className = "resident-app-card";
      const label = document.createElement("span");
      label.className = "resident-app-card-label";
      label.textContent = t(`resident_app.summary.${card.key}`);
      const value = document.createElement("strong");
      value.className = "resident-app-card-value";
      value.textContent = stringifyValue(card.value);
      item.append(label, value);
      cards.appendChild(item);
    }
  }

  function renderReviewItems(state: HomeScreenState): void {
    clearChildren(reviewItems);
    const orderedItems = prioritizeActiveReviewItem(
      state.top_review_items,
      activeReviewState.candidateId,
      (item) => (typeof item.candidate_id === "string" ? item.candidate_id : null),
    );
    for (const item of orderedItems) {
      const row = document.createElement("li");
      const rawCandidateId = typeof item.candidate_id === "string" ? item.candidate_id : null;
      const candidateId = rawCandidateId ?? t("resident_app.unknown");
      const summary =
        typeof item.display_summary === "string" && item.display_summary.trim()
          ? item.display_summary
          : t("resident_app.no_summary");
      row.appendChild(createResidentActionButton({
        label: `${candidateId} — ${summary}`,
        activeCandidateId: candidateId,
        disabled: rawCandidateId == null,
        onClick:
          rawCandidateId != null
            ? () => {
              daemonPanel.hidden = true;
              queuePanel.hidden = true;
              void showCandidateDetail(rawCandidateId);
            }
            : undefined,
      }));
      reviewItems.appendChild(row);
    }
    reviewItems.hidden = orderedItems.length === 0;
  }

  function renderDaemonActions(state: HomeScreenState): void {
    clearChildren(daemonActions);
    for (const action of state.top_daemon_actions) {
      appendResidentActionRow(daemonActions, {
        label:
          typeof action.command === "string" && action.command.trim()
            ? action.command
            : typeof action.label === "string" && action.label.trim()
              ? action.label
              : JSON.stringify(action),
        onClick: () => {
          void showDaemonPanel();
        },
      });
    }
    daemonActions.hidden = state.top_daemon_actions.length === 0;
  }

  function renderQuickLinks(state: HomeScreenState): void {
    clearChildren(quickLinks);
    const orderedLinks = [...state.quick_links];
    if (activeReviewState.candidateId) {
      orderedLinks.unshift({
        screen: "active_review_detail",
        path: `/app/ui/candidates/${activeReviewState.candidateId}`,
      });
    }
    const prioritizedLinks = prioritizeActiveReviewItem(
      orderedLinks,
      activeReviewState.candidateId ? "candidate_queue" : null,
      (link) => (link.screen === "candidate_queue" ? "candidate_queue" : null),
    );
    for (const link of prioritizedLinks) {
      const label = `${t(`resident_app.link.${link.screen}`)} → ${link.path}`;
      if (link.screen === "active_review_detail" && activeReviewState.candidateId) {
        appendResidentActionRow(quickLinks, {
          label,
          onClick: () => {
            daemonPanel.hidden = true;
            queuePanel.hidden = true;
            void showCandidateDetail(activeReviewState.candidateId!);
          },
        });
      } else if (link.screen === "candidate_queue") {
        appendResidentActionRow(quickLinks, {
          label,
          onClick: () => {
            void showCandidateQueue();
          },
        });
      } else if (link.screen === "daemon_panel") {
        appendResidentActionRow(quickLinks, {
          label,
          onClick: () => {
            void showDaemonPanel();
          },
        });
      } else {
        appendResidentActionRow(quickLinks, { label, disabled: true });
      }
    }
    quickLinks.hidden = prioritizedLinks.length === 0;
  }

  function renderDaemonPanelState(state: DaemonPanelScreenState): void {
    renderSummaryEntryList(
      daemonSummary,
      state.summary_cards.map((card) => ({
        key: t(`resident_app.daemon.${card.key}`),
        value: stringifyValue(card.value),
      })),
    );
    renderKeyValueRecord(daemonRuntime, state.runtime_init);
    renderKeyValueRecord(daemonCleanup, state.cleanup_preview);
    renderKeyValueRecord(daemonRepair, state.repair_preview);
    daemonPanel.hidden = false;
  }

  function buildQueueSummaryEntries(state: CandidateQueueScreenState): SummaryEntry[] {
    const activeCandidateId = activeReviewState.candidateId;
    const hasActiveCandidateInQueue = activeCandidateId
      ? state.items.some((item) => item.id === activeCandidateId)
      : false;

    const summaryEntries: SummaryEntry[] = [
      { key: t("resident_app.queue.reviewable_count"), value: String(state.reviewable_count) },
      { key: t("resident_app.queue.default_sort"), value: stringifyValue(state.default_sort) },
    ];
    if (activeCandidateId) {
      summaryEntries.push({
        key: t("resident_app.queue.active_candidate"),
        value: hasActiveCandidateInQueue
          ? t("resident_app.queue.active_present", { candidateId: activeCandidateId })
          : t("resident_app.queue.active_missing", { candidateId: activeCandidateId }),
      });
    }
    if (activeReviewState.sessionExists) {
      summaryEntries.push({
        key: t("resident_app.queue.active_source"),
        value: localizeReviewSessionSource(activeReviewState.source),
      });
      summaryEntries.push({
        key: t("resident_app.queue.active_count"),
        value: String(activeReviewState.count),
      });
    }
    for (const [statusKey, count] of Object.entries(state.status_counts)) {
      summaryEntries.push({
        key: `${t("resident_app.queue.status_prefix")} ${stringifyValue(statusKey)}`,
        value: String(count),
      });
    }
    return summaryEntries;
  }

  function renderQueuePanelState(state: CandidateQueueScreenState): void {
    lastQueueState = state;
    clearChildren(queueSections);
    clearChildren(queueItems);
    renderSummaryEntryList(queueSummary, buildQueueSummaryEntries(state));
    queueOpenActiveReviewButton.disabled = !activeReviewState.candidateId;
    queueOpenActiveReviewButton.title = activeReviewButtonReason();
    queueOpenActiveReviewButton.setAttribute("aria-label", activeReviewButtonReason());
    queueOpenActiveReviewButton.onclick = () => {
      if (!activeReviewState.candidateId) return;
      daemonPanel.hidden = true;
      queuePanel.hidden = true;
      void showCandidateDetail(activeReviewState.candidateId);
    };

    for (const section of state.top_sections) {
      const row = document.createElement("li");
      row.textContent = `${stringifyValue(section.section)}: ${section.count}`;
      queueSections.appendChild(row);
    }
    queueSections.hidden = state.top_sections.length === 0;

    const orderedItems = prioritizeActiveReviewItem(
      state.items,
      activeReviewState.candidateId,
      (item) => item.id,
    );
    for (const item of orderedItems.slice(0, 5)) {
      const summary =
        typeof item.display_summary === "string" && item.display_summary.trim()
          ? item.display_summary
          : item.content_preview;
      appendResidentActionRow(queueItems, {
        label: `${item.id} — ${summary}`,
        activeCandidateId: item.id,
        onClick: () => {
          daemonPanel.hidden = true;
          queuePanel.hidden = true;
          void showCandidateDetail(item.id);
        },
      });
    }
    queueItems.hidden = orderedItems.length === 0;
    queuePanel.hidden = false;
  }

  function renderRecordList(container: HTMLElement, payload: Record<string, unknown>): void {
    renderKeyValueRecord(container, payload);
  }

  function buildDetailActionEntries(state: CandidateDetailScreenState): SummaryEntry[] {
    return Object.entries(state.allowed_actions).map(([action, enabled]) => ({
      key: localizeFieldKey(action),
      value: stringifyValue(enabled),
    }));
  }

  function buildDetailActionHintEntries(state: CandidateDetailScreenState): string[] {
    const hints: string[] = [];
    if (state.allowed_actions.evaluate) {
      hints.push(t("resident_app.action_hint.evaluate"));
    }
    if (state.diff_available) {
      hints.push(t("resident_app.action_hint.diff"));
    }
    if (state.allowed_actions.approve) {
      hints.push(t("resident_app.action_hint.approve"));
    }
    if (state.allowed_actions.reject) {
      hints.push(t("resident_app.action_hint.reject"));
    }
    if (state.allowed_actions.revise) {
      hints.push(t("resident_app.action_hint.revise"));
    }
    return hints;
  }

  function renderDetailActionHints(state: CandidateDetailScreenState): void {
    renderPlainTextList(detailActionHints, buildDetailActionHintEntries(state));
  }

  function lineageSourceLabel(kind: string | null | undefined): string {
    if (kind === "selection") return t("review.lineage.source_selection");
    if (kind === "clipboard") return t("review.lineage.source_clipboard");
    if (kind === "page") return t("review.lineage.source_page");
    if (kind === "manual") return t("review.lineage.source_manual");
    return kind ?? "—";
  }

  function lineageDecisionLabel(decision: CandidateLineage["decision"]): string {
    const key = `review.lineage.decision_${decision}` as const;
    const label = t(key);
    return label === key ? decision : label;
  }

  function buildDetailLineageEntries(lineage: CandidateLineage): SummaryEntry[] {
    const entries: SummaryEntry[] = [
      [
        t("review.lineage.capture"),
        `${lineageSourceLabel(lineage.source_kind)} · ${lineage.captured_at.slice(0, 19)}`,
      ],
      [t("review.lineage.candidate"), lineage.candidate_id.slice(0, 12)],
      [t("review.lineage.decision"), lineageDecisionLabel(lineage.decision)],
    ].map(([key, value]) => ({ key, value }));
    if (activeReviewState.candidateId && activeReviewState.candidateId !== lineage.candidate_id) {
      entries.unshift({
        key: t("resident_app.detail.active_review_note"),
        value: t("resident_app.detail.active_review_mismatch", {
          candidateId: activeReviewState.candidateId,
        }),
      });
    }
    if (lineage.rde_class) {
      entries.push({ key: t("review.lineage.evaluation"), value: lineage.rde_class });
    } else if (lineage.evaluation_status) {
      entries.push({ key: t("review.lineage.evaluation"), value: lineage.evaluation_status });
    }
    if (lineage.operation) {
      entries.push({ key: t("review.lineage.operation"), value: lineage.operation });
    }
    if (lineage.context_path) {
      entries.push({ key: t("review.lineage.target"), value: lineage.context_path });
    }
    if (lineage.source_candidate_id) {
      entries.push({
        key: t("review.lineage.revised_from"),
        value: lineage.source_candidate_id.slice(0, 12),
      });
    }
    if (lineage.source_url) {
      entries.push({ key: t("resident_app.lineage.source_url"), value: lineage.source_url });
    }
    if (lineage.events.length > 0) {
      entries.push({ key: t("resident_app.lineage.events"), value: String(lineage.events.length) });
    }
    return entries;
  }

  function renderDetailLineage(lineage: CandidateLineage): void {
    const entries = buildDetailLineageEntries(lineage);
    renderSummaryEntryList(detailLineage, entries);
    detailLineage.hidden = entries.length === 0;
  }

  function buildDetailDiffEntries(candidateId: string, diff: CandidateDiff): SummaryEntry[] {
    const entries: SummaryEntry[] = [];
    if (activeReviewState.candidateId && activeReviewState.candidateId !== candidateId) {
      entries.push({
        key: t("resident_app.detail.active_review_note"),
        value: t("resident_app.detail.active_review_mismatch", {
          candidateId: activeReviewState.candidateId,
        }),
      });
    }
    const listDiff = listDiffFromBridgeDiff(diff);
    if (listDiff) {
      entries.push(
        { key: t("resident_app.diff.operation"), value: stringifyValue(listDiff.operation ?? "—") },
        {
          key: t("resident_app.diff.added"),
          value: listDiff.added.map((item) => stringifyValue(item)).join(", ") || "—",
        },
        {
          key: t("resident_app.diff.removed"),
          value: listDiff.removed.map((item) => stringifyValue(item)).join(", ") || "—",
        },
        {
          key: t("resident_app.diff.unchanged"),
          value:
            listDiff.unchanged.map((item) => stringifyValue(item)).join(", ")
            || String(listDiff.unchangedCount ?? listDiff.unchanged.length ?? 0),
        },
      );
      return entries;
    }
    entries.push({
      key: t("resident_app.diff.raw"),
      value: `${candidateId}: ${JSON.stringify(diff)}`,
    });
    return entries;
  }

  function renderDetailDiff(candidateId: string, diff: CandidateDiff): void {
    const entries = buildDetailDiffEntries(candidateId, diff);
    renderSummaryEntryList(detailDiff, entries);
    detailDiff.hidden = entries.length === 0;
  }

  function buildDetailSummaryEntries(
    candidateId: string,
    state: CandidateDetailScreenState,
  ): SummaryEntry[] {
    const summaryEntries: SummaryEntry[] = [
      { key: t("resident_app.detail.candidate_id"), value: candidateId },
      {
        key: t("resident_app.detail.active_review"),
        value:
          activeReviewState.candidateId === candidateId
            ? t("resident_app.value.true")
            : t("resident_app.value.false"),
      },
      {
        key: t("resident_app.detail.active_source"),
        value: localizeReviewSessionSource(activeReviewState.source),
      },
      {
        key: t("resident_app.detail.active_count"),
        value: String(activeReviewState.count),
      },
      {
        key: t("resident_app.detail.active_review_note"),
        value:
          activeReviewState.candidateId && activeReviewState.candidateId !== candidateId
            ? t("resident_app.detail.active_review_mismatch", {
              candidateId: activeReviewState.candidateId,
            })
            : t("resident_app.detail.active_review_match"),
      },
      { key: t("resident_app.detail.diff_available"), value: stringifyValue(state.diff_available) },
    ];
    for (const [key, value] of Object.entries(state.ui_summary)) {
      summaryEntries.push({ key: localizeFieldKey(key), value: stringifyValue(value) });
    }
    return summaryEntries;
  }

  function renderDetailPanelState(candidateId: string, state: CandidateDetailScreenState): void {
    lastDetailCandidateId = candidateId;
    lastDetailState = state;
    clearChildren(detailActions);
    renderRecordList(detailProposal, state.proposal);
    renderRecordList(detailEvaluation, state.evaluation);
    renderDetailActionHints(state);
    renderSummaryEntryList(detailSummary, buildDetailSummaryEntries(candidateId, state));
    renderSummaryEntryList(detailActions, buildDetailActionEntries(state));
    detailActions.hidden = Object.keys(state.allowed_actions).length === 0;
    detailContent.textContent = state.content?.trim() || t("resident_app.no_content");
    detailDiff.hidden = !state.diff_available;
    detailLineage.hidden = true;
    detailReviewButton.onclick = () => {
      void (async () => {
        await focusCandidate(candidateId);
        await syncActiveReviewState(candidateId);
      })();
    };
    detailQueueButton.onclick = () => {
      void showCandidateQueue();
    };
    detailActiveReviewButton.disabled =
      !activeReviewState.candidateId || activeReviewState.candidateId === candidateId;
    detailActiveReviewButton.title = activeReviewButtonReason(candidateId);
    detailActiveReviewButton.setAttribute("aria-label", activeReviewButtonReason(candidateId));
    detailActiveReviewButton.onclick = () => {
      if (!activeReviewState.candidateId || activeReviewState.candidateId === candidateId) return;
      void showCandidateDetail(activeReviewState.candidateId);
    };
    detailPanel.hidden = false;
  }

  function renderState(state: HomeScreenState): void {
    lastHomeState = state;
    renderCards(state);
    renderReviewItems(state);
    renderDaemonActions(state);
    renderQuickLinks(state);
    panel.hidden = false;
    status.textContent = "";
  }

  async function showDaemonPanel(): Promise<void> {
    detailPanel.hidden = true;
    queuePanel.hidden = true;
    status.textContent = t("resident_app.daemon_loading");
    try {
      const state = await readDaemonPanelScreenState(send);
      renderDaemonPanelState(state);
      status.textContent = "";
    } catch (error) {
      status.textContent =
        typeof error === "object" && error !== null && "error" in error
          ? formatBridgeError(error as Extract<BackgroundResponse, { ok: false }>)
          : `${t("resident_app.daemon_unavailable")} ${String(error)}`;
    }
  }

  async function showCandidateQueue(): Promise<void> {
    detailPanel.hidden = true;
    daemonPanel.hidden = true;
    status.textContent = t("resident_app.queue_loading");
    try {
      await syncActiveReviewState();
      const state = await readCandidateQueueScreenState(send);
      renderQueuePanelState(state);
      status.textContent = "";
    } catch (error) {
      status.textContent =
        typeof error === "object" && error !== null && "error" in error
          ? formatBridgeError(error as Extract<BackgroundResponse, { ok: false }>)
          : `${t("resident_app.queue_unavailable")} ${String(error)}`;
    }
    await loadCandidateQueue();
  }

  async function showCandidateDetail(candidateId: string): Promise<void> {
    daemonPanel.hidden = true;
    queuePanel.hidden = true;
    status.textContent = t("resident_app.detail_loading");
    try {
      await syncActiveReviewState(candidateId);
      const state = await readCandidateDetailScreenState(send, candidateId);
      renderDetailPanelState(candidateId, state);
      if (state.diff_available) {
        const diff = await readCandidateDiff(send, candidateId);
        renderDetailDiff(candidateId, diff);
      }
      const lineage = await readCandidateLineage(send, candidateId);
      renderDetailLineage(lineage);
      status.textContent = "";
      await focusCandidate(candidateId);
      await syncActiveReviewState(candidateId);
    } catch (error) {
      status.textContent = formatDetailUnavailable(error);
    }
  }

  async function refresh(): Promise<void> {
    panel.hidden = false;
    detailPanel.hidden = true;
    queuePanel.hidden = true;
    daemonPanel.hidden = true;
    status.textContent = t("resident_app.loading");
    try {
      const [contract, state] = await Promise.all([
        readAppContract(send),
        readHomeScreenState(send),
      ]);
      renderContract(contract);
      await syncActiveReviewState();
      renderState(state);
    } catch (error) {
      status.textContent =
        typeof error === "object" && error !== null && "error" in error
          ? formatBridgeError(error as Extract<BackgroundResponse, { ok: false }>)
          : `${t("resident_app.unavailable")} ${String(error)}`;
    }
  }

  async function refreshVisibleState(): Promise<void> {
    if (!panel.hidden && !detailPanel.hidden && lastDetailCandidateId) {
      status.textContent = t("resident_app.detail_loading");
      try {
        const detailState = await readCandidateDetailScreenState(send, lastDetailCandidateId);
        renderDetailPanelState(lastDetailCandidateId, detailState);
        if (detailState.diff_available) {
          const diff = await readCandidateDiff(send, lastDetailCandidateId);
          renderDetailDiff(lastDetailCandidateId, diff);
        } else {
          clearChildren(detailDiff);
          detailDiff.hidden = true;
        }
        const lineage = await readCandidateLineage(send, lastDetailCandidateId);
        renderDetailLineage(lineage);
        status.textContent = "";
        return;
      } catch (error) {
        await fallbackToQueueAfterDetailFailure(error);
        return;
      }
    }
    if (!panel.hidden && !queuePanel.hidden) {
      status.textContent = t("resident_app.queue_loading");
      try {
        const queueState = await readCandidateQueueScreenState(send);
        renderQueuePanelState(queueState);
        status.textContent = "";
        return;
      } catch (error) {
        status.textContent =
          typeof error === "object" && error !== null && "error" in error
            ? formatBridgeError(error as Extract<BackgroundResponse, { ok: false }>)
            : `${t("resident_app.queue_unavailable")} ${String(error)}`;
        return;
      }
    }
    if (!panel.hidden && !daemonPanel.hidden) {
      return;
    }
    if (lastHomeState) {
      status.textContent = t("resident_app.loading");
      try {
        const homeState = await readHomeScreenState(send);
        renderState(homeState);
        status.textContent = "";
      } catch (error) {
        status.textContent =
          typeof error === "object" && error !== null && "error" in error
            ? formatBridgeError(error as Extract<BackgroundResponse, { ok: false }>)
            : `${t("resident_app.unavailable")} ${String(error)}`;
      }
    }
  }

  async function handleCandidatesChanged(candidateId: string | null): Promise<void> {
    await syncActiveReviewState(candidateId ?? undefined);
    await refreshVisibleState();
  }

  return { refresh, showDaemonPanel, showCandidateQueue, handleCandidatesChanged };
}
