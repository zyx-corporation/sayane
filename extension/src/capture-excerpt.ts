/**
 * Capture excerpt vs stored profile content — keep review UI responsibilities separate.
 */

import {
  countImportantTermsInCapture,
  IMPORTANT_TERMS_CLIPBOARD_WARN_THRESHOLD,
} from "./clipboard-preview.js";
import type { CandidateReviewSession } from "./review-session.js";
import type { CandidateDetail } from "./types.js";

export const CAPTURE_EXCERPT_MAX = 1200;

const PERSONA_ROOT_CAPTURE_RE = /^persona\s*:/im;

export type CaptureExcerptSession = Pick<
  CandidateReviewSession,
  "captureId" | "candidateIds" | "rawCaptureText"
>;

export function candidateInReviewSession(
  detailId: string,
  session?: CaptureExcerptSession | null,
): boolean {
  if (!session) return false;
  if (session.captureId === detailId) return true;
  return session.candidateIds?.includes(detailId) ?? false;
}

/** Never use `detail.content` — it is not guaranteed to be raw capture input. */
export function captureExcerptForReview(
  detail: CandidateDetail,
  session?: CaptureExcerptSession | null,
): string {
  const inSession = candidateInReviewSession(detail.id, session);
  const sessionText = inSession ? session?.rawCaptureText?.trim() ?? "" : "";
  if (sessionText) {
    return sessionText.slice(0, CAPTURE_EXCERPT_MAX);
  }
  return captureExcerptFromDetail(detail);
}

export function captureExcerptFromDetail(detail: CandidateDetail): string {
  const fromApi = detail.source_excerpt?.trim();
  if (fromApi) return fromApi.slice(0, CAPTURE_EXCERPT_MAX);

  const raw = detail.raw_capture?.trim();
  if (raw) return raw.slice(0, CAPTURE_EXCERPT_MAX);

  const cleaned = detail.cleaned_capture?.trim();
  if (cleaned) return cleaned.slice(0, CAPTURE_EXCERPT_MAX);

  const summary = detail.display_summary?.trim();
  if (summary) return summary.slice(0, CAPTURE_EXCERPT_MAX);

  return "";
}

export function excerptHasPersonaRoot(text: string): boolean {
  return PERSONA_ROOT_CAPTURE_RE.test(text.trim());
}

export function captureExcerptLineCount(text: string): number {
  if (!text.trim()) return 0;
  return text.split(/\r?\n/).length;
}

/** Proposal scope looks like full persona while raw excerpt does not. */
/** True when capture lists many terms (likely full file paste, not a short edit). */
export function detectImportantTermsLargeCapture(
  excerpt: string,
  termThreshold = IMPORTANT_TERMS_CLIPBOARD_WARN_THRESHOLD,
): boolean {
  return countImportantTermsInCapture(excerpt) > termThreshold;
}

export function detectCaptureScopeMismatch(
  detail: CandidateDetail,
  excerpt: string,
): boolean {
  const section = detail.proposal.section ?? "";
  const itemCount = detail.proposal.items?.length ?? 0;
  const lines = captureExcerptLineCount(excerpt);
  if (section === "important_terms") return false;
  if (itemCount <= 15) return false;
  if (section === "persona" || section === "mixed_sections") {
    if (lines > 0 && lines < 30 && !excerptHasPersonaRoot(excerpt)) return true;
    if (lines > 0 && lines < 30 && itemCount > lines * 3) return true;
  }
  return false;
}

export function filterProposalItemsForSection(
  detail: CandidateDetail,
): Array<Record<string, unknown>> {
  const section = detail.proposal.section ?? "";
  const items = (detail.proposal.items ?? []) as Array<Record<string, unknown>>;
  if (section === "important_terms") {
    return items.filter((item) => {
      const path = String(item.yaml_path ?? item.path ?? "").toLowerCase();
      const sec = String(item.section ?? "").toLowerCase();
      return path.includes("important_terms") || sec === "important_terms";
    });
  }
  return items;
}

/** Limit stored-context diff lines to the candidate target section. */
export function filterStoredContextForSection(
  items: unknown[],
  section: string,
): unknown[] {
  if (!section || section === "mixed_sections" || section === "review_required") {
    return items;
  }
  if (section === "important_terms") {
    const denyPersonaPath =
      /preferred_name|organization\.|location\.|email|development_preferences|persona\./i;
    return items.filter((item) => {
      const path = diffItemPath(item);
      if (!path) return true;
      return !denyPersonaPath.test(path);
    });
  }
  const needle = section.toLowerCase();
  return items.filter((item) => {
    const path = diffItemPath(item).toLowerCase();
    return path.includes(needle);
  });
}

function diffItemPath(item: unknown): string {
  if (typeof item === "string") return item;
  if (item && typeof item === "object") {
    const o = item as Record<string, unknown>;
    return String(o.path ?? o.yaml_path ?? o.name ?? "");
  }
  return String(item);
}
