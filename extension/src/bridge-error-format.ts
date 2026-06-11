/**
 * Map Bridge / Core errors to user-facing messages (never show raw internal text).
 */

import { categoryLabel, type CandidateCategory } from "./candidate-display.js";
import { getLocale, t } from "./i18n.js";
import type { SupportedLocale } from "./types.js";

const UNSUPPORTED_MERGE_RE = /^Unsupported merge section:\s*(.+)$/i;
const MERGE_NOT_ALLOWED_RE = /^Merge to '([^']+)' is not allowed/i;
const MERGE_REQUIRES_FORCE_RE = /^Cannot merge section '([^']+)' without/i;

export type BridgeErrorLike = { message: string; details?: Record<string, unknown> };

/** User-facing message only — never expose raw Core/Bridge text in normal UI. */
export function toUserFacingError(error: BridgeErrorLike, locale?: SupportedLocale): string {
  return formatUserFacingBridgeError(
    error.message,
    error.details,
    locale,
  );
}

export function formatUserFacingBridgeError(
  error: string,
  details?: Record<string, unknown>,
  locale?: SupportedLocale,
): string {
  const loc = locale ?? getLocale();

  if (details && details.error === "unsafe_rde_category") {
    const category = String(details.rde_category ?? "unknown");
    const label = categoryLabel(category as CandidateCategory, loc);
    if (loc === "ja") {
      return `この更新候補は「${label}」と評価されているため、そのまま承認できません。`;
    }
    return t("error.unsafe_rde_category", { category: label });
  }

  if (details && details.error === "requires_force_critical") {
    return t("error.requires_force_critical", {
      section: String(details.section ?? ""),
    });
  }

  if (
    details
    && (details.error === "explicit_confirmation_required"
      || details.error === "explicit_confirmation_reason_required")
  ) {
    return t("review.approve_explicit_check_and_reason");
  }

  if (details && details.error === "invalid_candidate_transition") {
    if (typeof details.message === "string") {
      return mapKnownCoreMessage(details.message, loc);
    }
    return t("error.invalid_candidate_transition");
  }

  const fromDetails =
    typeof details?.message === "string" ? details.message : error;
  return mapKnownCoreMessage(fromDetails, loc);
}

export function mapKnownCoreMessage(message: string, locale?: SupportedLocale): string {
  const trimmed = message.trim();
  if (!trimmed) return t("error.generic");

  const unsupported = UNSUPPORTED_MERGE_RE.exec(trimmed);
  if (unsupported) {
    const section = unsupported[1].trim();
    const short = t("error.merge_section_unsupported_short");
    if (short !== "error.merge_section_unsupported_short") {
      return short;
    }
    if (locale === "ja") {
      return "この更新候補はまだ自動保存に対応していない種類です。保存先セクションの対応が必要です。";
    }
    const named = t("error.merge_section_unsupported_named", { section });
    if (named !== "error.merge_section_unsupported_named") {
      return named;
    }
    return `Section "${section}" is not supported for automatic save yet.`;
  }

  const notAllowed = MERGE_NOT_ALLOWED_RE.exec(trimmed);
  if (notAllowed) {
    return t("detail.merge_section_blocked", { section: notAllowed[1].trim() });
  }

  const needsForce = MERGE_REQUIRES_FORCE_RE.exec(trimmed);
  if (needsForce) {
    return t("error.requires_force_critical", { section: needsForce[1].trim() });
  }

  const known: Record<string, string> = {
    "Bridge token not configured. Set it in Options.": "error.bridge_token",
    "No text selected": "status.no_text_selected",
    "Could not read page": "status.could_not_read_page",
    "No active tab": "error.no_active_tab",
    "Cannot capture on this page. Open a normal https:// page (e.g. https://example.com), select text, reload the tab if you just updated the extension, then try again.":
      "error.restricted_page",
    "This candidate is not in evaluated state and cannot be approved. Evaluate it first.":
      "error.approve_requires_evaluate",
  };
  const key = known[trimmed];
  if (key) return t(key);

  if (locale === "ja") {
    const jaTemplate = "この更新候補はまだ自動保存に対応していない種類です。保存先セクションの対応が必要です。";
    const fromCatalog = t("error.generic");
    return fromCatalog === "error.generic" ? jaTemplate : fromCatalog;
  }
  const generic = t("error.generic");
  return generic === "error.generic"
    ? "The operation failed. Restart the Bridge or try again shortly."
    : generic;
}
