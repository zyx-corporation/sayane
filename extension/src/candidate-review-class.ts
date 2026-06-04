/** UI-facing review classification for candidate list filtering. */

import { getApproveAvailability } from "./approve-availability.js";
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

const PERSONA_DOC_HEADER = /^#\s*.+(ペルソナ|persona)/im;
const PERSONA_BASIC_INFO = /^##\s*基本情報/m;

export function isPersonaDump(text: string, section: string): boolean {
  if (section === "important_terms") return false;
  const trimmed = text.trim();
  if (/^important_terms\s*:/im.test(trimmed) && !/^persona\s*:/im.test(trimmed)) {
    return false;
  }
  if (section === "mixed_sections" || section === "review_required") {
    return text.length > 400 && /^persona\s*:/im.test(trimmed);
  }
  if (PERSONA_DOC_HEADER.test(text)) return true;
  if (PERSONA_BASIC_INFO.test(text) && text.length > 200) return true;
  if (section === "voice.tone" && /^#\s/m.test(text) && text.length > 300) {
    return true;
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

  if (section === "important_terms") {
    if (c.status === "evaluated") {
      const rde = c.rde_class;
      if (rde === "Preserved") return "duplicate_or_confirmed";
      if (rde === "Critical Distortion" || rde === "Suspicious Drift") {
        return "reject_recommended";
      }
    }
    return "new_candidate";
  }

  if (isPersonaDump(preview, section)) {
    return "sensitive_review";
  }

  if (section === "review_required" || section === "mixed_sections") {
    return "sensitive_review";
  }

  if (c.status === "evaluated") {
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
    return "new_candidate";
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

export function shouldBlockBulkApprove(c: CandidateSummary): boolean {
  const preview = c.content_preview ?? "";
  const section = c.section ?? "";
  if (isPersonaDump(preview, section)) return true;
  const cls = classifyCandidate(c);
  return cls === "reject_recommended" || cls === "sensitive_review";
}

export function riskHintKey(cls: CandidateReviewClass): string {
  return `review.risk.${cls}`;
}

export function riskHintKeyForCandidate(c: CandidateSummary): string {
  if (c.section === "important_terms") {
    const withSummary = c as CandidateSummary & { display_summary?: string | null };
    const summary = withSummary.display_summary ?? c.content_preview ?? "";
    if (/追加候補|term\(s\) to add/i.test(summary)) {
      return "review.risk.important_terms_add";
    }
  }
  return riskHintKey(classifyCandidate(c));
}

export function recommendedActionKeyForCandidate(c: CandidateSummary): string {
  const cls = classifyCandidate(c);

  if (c.status === "pending") {
    return c.section === "important_terms"
      ? "review.action.evaluate_before_approve"
      : "review.action.new_candidate";
  }

  const avail = getApproveAvailability(c, undefined, { compact: true });

  if (avail.kind === "resolved") {
    return cls === "duplicate_or_confirmed"
      ? "review.action.no_approve_needed"
      : "review.action.low_value";
  }

  if (avail.kind === "needs_evaluation") {
    return "review.action.evaluate_before_approve";
  }

  if (avail.kind === "blocked") {
    if (cls === "reject_recommended") return "review.action.reject_recommended";
    if (cls === "sensitive_review") return "review.action.sensitive_review";
    if (cls === "duplicate_or_confirmed") return "review.action.no_approve_needed";
    return "review.action.sensitive_review";
  }

  if (avail.kind === "requires_override") {
    return "review.action.sensitive_review";
  }

  if (avail.kind === "needs_explicit_confirmation") {
    return "review.action.explicit_confirm_before_approve";
  }

  if (avail.kind === "can_approve") {
    if (
      c.section === "important_terms"
      && (cls === "new_candidate" || cls === "meaning_changed")
    ) {
      return "review.action.important_terms_add";
    }
    if (cls === "duplicate_or_confirmed") {
      return "review.action.no_approve_needed";
    }
    return recommendedActionKey(cls);
  }

  return recommendedActionKey(cls);
}
