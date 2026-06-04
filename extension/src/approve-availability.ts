/**
 * Single source of truth for Candidate Review approve button state and labels.
 */

import {
  canApproveWithCriticalOverride,
  categoryLabel,
  type CandidateCategory,
} from "./candidate-display.js";
import { shouldBlockBulkApprove } from "./candidate-review-class.js";
import {
  isAutoMergeSupported,
  isBlockedMergeSection,
  isCriticalSection,
  requiresExplicitContextConfirmation,
  requiresForceCriticalMerge,
} from "./merge-policy.js";
import {
  type CandidateActionState,
  isBusyActionState,
  isResolvedActionState,
} from "./candidate-action-state.js";
import type { CandidateDetail, CandidateSummary, SupportedLocale } from "./types.js";

export type ApproveAvailabilityKind =
  | "needs_evaluation"
  | "needs_explicit_confirmation"
  | "can_approve"
  | "requires_override"
  | "blocked"
  | "resolved";

export type ExplicitConfirmationState = {
  checked: boolean;
  reason: string;
};

export type OverrideConfirmationState = {
  required: boolean;
  checked: boolean;
  reason: string;
};

export type ApproveAvailabilityOptions = {
  /** Collapsed card quick action (stricter: no pending / no override-only path). */
  compact?: boolean;
  cardActionState?: CandidateActionState;
  explicitConfirmation?: ExplicitConfirmationState;
  overrideConfirmation?: OverrideConfirmationState;
};

export type ApproveAvailability = {
  kind: ApproveAvailabilityKind;
  enabled: boolean;
  labelKey: string;
  reasonKey?: string;
};

export function effectiveCandidateStatus(
  c: CandidateSummary,
  detail?: CandidateDetail,
): CandidateSummary["status"] {
  return detail?.status ?? c.status;
}

export function candidateCategoryForApprove(
  c: CandidateSummary,
  detail?: CandidateDetail,
): CandidateCategory | null {
  const raw = detail?.evaluation?.rde_class ?? c.rde_class ?? null;
  return raw as CandidateCategory | null;
}

function approveBlockedByRdeReasonKey(category: CandidateCategory | null): string {
  switch (category) {
    case "Preserved":
      return "review.approve_blocked_rde_preserved";
    case "Unresolved Gap":
      return "review.approve_blocked_rde_unresolved_gap";
    case "Suspicious Drift":
      return "review.approve_blocked_rde_suspicious_drift";
    case "Critical Distortion":
      return "review.approve_blocked_rde_critical_distortion";
    default:
      return "review.approve_blocked_after_eval";
  }
}

/** User-visible explanation when the approve button is disabled. */
export function approveUnavailableMessage(
  c: CandidateSummary,
  detail: CandidateDetail | undefined,
  avail: ApproveAvailability,
  locale: SupportedLocale,
  translate: (key: string, params?: Record<string, string | number>) => string,
): string {
  const key = avail.reasonKey ?? "review.approve_unavailable_generic";
  const category = candidateCategoryForApprove(c, detail);
  if (
    category
    && (key === "review.approve_blocked_after_eval" || key.startsWith("review.approve_blocked_rde_"))
  ) {
    return translate(approveBlockedByRdeReasonKey(category), {
      category: categoryLabel(category, locale),
    });
  }
  return translate(key);
}

function explicitConfirmationReasonKey(
  state?: ExplicitConfirmationState,
): string {
  const hasReason = (state?.reason?.trim() ?? "").length > 0;
  if (!state?.checked && !hasReason) {
    return "review.approve_explicit_check_and_reason";
  }
  if (!state?.checked) {
    return "review.approve_explicit_check_required";
  }
  if (!hasReason) {
    return "review.approve_explicit_reason_required";
  }
  return "review.approve_explicit_check_and_reason";
}

function explicitConfirmationSatisfied(
  section: string,
  state?: ExplicitConfirmationState,
): boolean {
  if (!requiresExplicitContextConfirmation(section)) return true;
  if (!state?.checked) return false;
  return (state.reason?.trim() ?? "").length > 0;
}

function overrideConfirmationSatisfied(
  state?: OverrideConfirmationState,
): boolean {
  if (!state?.required) return true;
  if (!state.checked) return false;
  return (state.reason?.trim() ?? "").length > 0;
}

function overrideReasonKey(state?: OverrideConfirmationState): string {
  if (!state?.required) return "detail.critical_override_required";
  if (!state.checked) return "detail.critical_override_required";
  if (!(state.reason?.trim() ?? "")) {
    return "detail.critical_override_reason_required";
  }
  return "detail.critical_override_required";
}

export function readApproveContextFromActions(
  actionsEl: HTMLElement | null | undefined,
): Pick<ApproveAvailabilityOptions, "explicitConfirmation" | "overrideConfirmation"> {
  if (!actionsEl) return {};

  const needsExplicit = actionsEl.dataset.requiresExplicitConfirmation === "1";
  const needsOverride =
    actionsEl.dataset.hasCriticalRde === "1"
    || actionsEl.dataset.hasCriticalSection === "1";

  const explicitCheck = actionsEl.querySelector<HTMLInputElement>(
    ".explicit-confirm-check",
  );
  const explicitReason = actionsEl.querySelector<HTMLInputElement>(
    ".explicit-confirm-reason",
  );
  const overrideCheck = actionsEl.querySelector<HTMLInputElement>(".override-check");
  const overrideReason = actionsEl.querySelector<HTMLInputElement>(".override-reason");

  return {
    explicitConfirmation: needsExplicit
      ? {
          checked: Boolean(explicitCheck?.checked),
          reason: explicitReason?.value ?? "",
        }
      : undefined,
    overrideConfirmation: needsOverride
      ? {
          required: true,
          checked: Boolean(overrideCheck?.checked),
          reason: overrideReason?.value ?? "",
        }
      : undefined,
  };
}

/** Read confirmation fields from the expanded actions panel containing this button. */
export function readApproveContextFromButton(
  btn: HTMLButtonElement | null | undefined,
): Pick<ApproveAvailabilityOptions, "explicitConfirmation" | "overrideConfirmation"> {
  const actionsEl = btn?.closest<HTMLElement>(".card-expanded-actions") ?? null;
  return readApproveContextFromActions(actionsEl);
}

export function getApproveAvailability(
  c: CandidateSummary,
  detail?: CandidateDetail,
  options?: ApproveAvailabilityOptions,
): ApproveAvailability {
  const compact = options?.compact ?? false;
  const cardActionState = options?.cardActionState ?? "idle";
  const status = effectiveCandidateStatus(c, detail);
  const section = detail?.proposal?.section ?? c.section ?? "";
  const category = candidateCategoryForApprove(c, detail);

  if (status === "approved" || status === "rejected") {
    return {
      kind: "resolved",
      enabled: false,
      labelKey: "candidate.approve",
      reasonKey: status === "approved"
        ? "review.approve_already_approved"
        : "review.approve_already_rejected",
    };
  }

  if (isResolvedActionState(cardActionState)) {
    return {
      kind: "resolved",
      enabled: false,
      labelKey: "candidate.approve",
    };
  }

  if (isBusyActionState(cardActionState)) {
    const labelKey =
      cardActionState === "approving" ? "busy.approving" : "candidate.approve";
    return {
      kind: "blocked",
      enabled: false,
      labelKey,
    };
  }

  if (!isAutoMergeSupported(section)) {
    return {
      kind: "blocked",
      enabled: false,
      labelKey: "candidate.approve",
      reasonKey: "error.merge_section_unsupported",
    };
  }

  if (isBlockedMergeSection(section)) {
    return {
      kind: "blocked",
      enabled: false,
      labelKey: "candidate.approve",
      reasonKey: "detail.merge_section_blocked",
    };
  }

  if (compact && shouldBlockBulkApprove(c)) {
    return {
      kind: "blocked",
      enabled: false,
      labelKey: "candidate.approve",
      reasonKey: "review.approve_blocked_hint",
    };
  }

  if (status === "pending") {
    return {
      kind: "needs_evaluation",
      enabled: false,
      labelKey: "candidate.approve",
      reasonKey: "review.approve_requires_evaluation",
    };
  }

  if (!explicitConfirmationSatisfied(section, options?.explicitConfirmation)) {
    return {
      kind: "needs_explicit_confirmation",
      enabled: false,
      labelKey: "candidate.approve",
      reasonKey: explicitConfirmationReasonKey(options?.explicitConfirmation),
    };
  }

  const needsRdeOverride = category === "Critical Distortion";
  const needsSectionOverride =
    requiresForceCriticalMerge(section) && isCriticalSection(section);

  if (needsRdeOverride || needsSectionOverride) {
    const overrideState: OverrideConfirmationState = options?.overrideConfirmation ?? {
      required: true,
      checked: false,
      reason: "",
    };
    if (!overrideConfirmationSatisfied({ ...overrideState, required: true })) {
      return {
        kind: "requires_override",
        enabled: false,
        labelKey: "candidate.approve",
        reasonKey: overrideReasonKey(overrideState),
      };
    }
    if (!canApproveWithCriticalOverride(status, category)) {
      return {
        kind: "blocked",
        enabled: false,
        labelKey: "candidate.approve",
        reasonKey: approveBlockedByRdeReasonKey(category),
      };
    }
    return {
      kind: "can_approve",
      enabled: true,
      labelKey: "candidate.approve",
    };
  }

  if (!canApproveWithCriticalOverride(status, category)) {
    return {
      kind: "blocked",
      enabled: false,
      labelKey: "candidate.approve",
      reasonKey: approveBlockedByRdeReasonKey(category),
    };
  }

  return {
    kind: "can_approve",
    enabled: true,
    labelKey: "candidate.approve",
  };
}

export function canApproveCandidate(
  c: CandidateSummary,
  detail?: CandidateDetail,
  options?: ApproveAvailabilityOptions,
): boolean {
  const avail = getApproveAvailability(c, detail, options);
  return avail.kind === "can_approve" && avail.enabled;
}

export function canQuickApprove(
  c: CandidateSummary,
  detail?: CandidateDetail,
): boolean {
  if (effectiveCandidateStatus(c, detail) !== "evaluated") return false;
  const avail = getApproveAvailability(c, detail, { compact: true });
  return avail.kind === "can_approve" && avail.enabled;
}

export function syncSummaryFromDetail(
  summary: CandidateSummary,
  detail?: CandidateDetail,
): void {
  if (!detail) return;
  if (detail.status) summary.status = detail.status;
  const rde = detail.evaluation?.rde_class;
  if (rde) summary.rde_class = rde;
}
