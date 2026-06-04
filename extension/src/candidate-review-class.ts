/** UI-facing review classification for candidate list filtering. */

import type { CandidateSummary } from "./types.js";

export type CandidateReviewClass =
  | "reject_recommended"
  | "sensitive_review"
  | "conflict"
  | "meaning_changed"
  | "inferred_extension"
  | "new_candidate"
  | "duplicate_or_confirmed"
  | "low_value"
  | "debug_only";

export type ReviewFilterId =
  | "review_required"
  | "all"
  | "reject_recommended"
  | "has_diff"
  | "inferred_extension"
  | "low_value"
  | "debug";

export const REVIEW_REQUIRED_CLASSES: CandidateReviewClass[] = [
  "reject_recommended",
  "sensitive_review",
  "conflict",
  "meaning_changed",
  "inferred_extension",
  "new_candidate",
];

const PERSONA_MARKERS =
  /persona\s*:|communication_mode|writing_style|identity\s*:|values\.|major_projects\s*:/i;

export function isPersonaDump(text: string, section: string): boolean {
  if (section === "mixed_sections" || section === "review_required") {
    return text.length > 400;
  }
  if (text.length > 1500 && PERSONA_MARKERS.test(text)) return true;
  if (/^---\s*$/m.test(text) && text.length > 800) return true;
  if (/^persona\s*:/im.test(text)) return true;
  return false;
}

export function classifyCandidate(c: CandidateSummary): CandidateReviewClass {
  const section = c.section ?? "";
  const preview = c.content_preview ?? "";

  if (c.evaluation_status === "judge_failed") {
    return "debug_only";
  }

  if (c.status === "approved" || c.status === "rejected") {
    return "low_value";
  }

  if (isPersonaDump(preview, section)) {
    return "sensitive_review";
  }

  if (section === "review_required" || section === "mixed_sections") {
    return "sensitive_review";
  }

  const rde = c.rde_class;
  if (rde === "Critical Distortion" || rde === "Suspicious Drift") {
    return "reject_recommended";
  }
  if (rde === "Preserved") {
    return "duplicate_or_confirmed";
  }
  if (rde === "Authorized Transformation") {
    return "meaning_changed";
  }
  if (rde === "Inferred Extension") {
    return "inferred_extension";
  }
  if (rde === "Unresolved Gap") {
    return "conflict";
  }

  if (c.status === "pending") {
    return "new_candidate";
  }

  return "low_value";
}

export function matchesReviewFilter(
  c: CandidateSummary,
  filter: ReviewFilterId,
): boolean {
  const cls = classifyCandidate(c);
  switch (filter) {
    case "review_required":
      return REVIEW_REQUIRED_CLASSES.includes(cls);
    case "all":
      return cls !== "debug_only";
    case "reject_recommended":
      return cls === "reject_recommended";
    case "has_diff":
      return (
        cls === "conflict"
        || cls === "meaning_changed"
        || cls === "sensitive_review"
        || cls === "new_candidate"
        || cls === "inferred_extension"
        || cls === "reject_recommended"
      );
    case "inferred_extension":
      return cls === "inferred_extension";
    case "low_value":
      return cls === "low_value" || cls === "duplicate_or_confirmed";
    case "debug":
      return cls === "debug_only";
    default:
      return true;
  }
}

export function reviewClassLabelKey(cls: CandidateReviewClass): string {
  return `review.class.${cls}`;
}

export function recommendedActionKey(cls: CandidateReviewClass): string {
  return `review.action.${cls}`;
}

export function riskHintKey(cls: CandidateReviewClass): string {
  return `review.risk.${cls}`;
}
