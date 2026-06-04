/**
 * Current Candidate Review session — one capture replaces the active review list.
 * Bridge persists all candidates; the extension UI shows only the current session.
 */

import type { CandidateSummary } from "./types.js";

export type ReviewCaptureSource = "selection" | "clipboard" | "page" | "manual";

export type CandidateReviewSession = {
  captureId: string;
  source: ReviewCaptureSource;
  capturedAt: string;
  profileId: string;
  candidateIds: string[];
  /** Raw input from this capture (selection / clipboard / page), not stored Profile IR. */
  rawCaptureText: string;
};

export const CURRENT_REVIEW_SESSION_KEY = "sayane.currentReviewSession";
export const CANDIDATES_TICK_KEY = "sayane.candidatesTick";
export const CANDIDATES_FOCUS_KEY = "sayane.candidatesFocusId";

export function parseReviewSession(raw: unknown): CandidateReviewSession | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const source = o.source;
  if (
    source !== "selection"
    && source !== "clipboard"
    && source !== "page"
    && source !== "manual"
  ) {
    return null;
  }
  const captureId = o.captureId;
  const capturedAt = o.capturedAt;
  const profileId = o.profileId;
  const candidateIds = o.candidateIds;
  if (typeof captureId !== "string" || !captureId) return null;
  if (typeof capturedAt !== "string" || !capturedAt) return null;
  if (typeof profileId !== "string" || !profileId) return null;
  if (!Array.isArray(candidateIds) || candidateIds.length === 0) return null;
  if (!candidateIds.every((id) => typeof id === "string" && id.length > 0)) {
    return null;
  }
  const rawCaptureText = o.rawCaptureText;
  return {
    captureId,
    source,
    capturedAt,
    profileId,
    candidateIds: candidateIds as string[],
    rawCaptureText: typeof rawCaptureText === "string" ? rawCaptureText : "",
  };
}

/** Keep only candidates that belong to the current review session.
 * When no session is active, show all candidates (graceful fallback). */
export function filterCandidatesForReviewSession(
  bridgeCandidates: CandidateSummary[],
  session: CandidateReviewSession | null,
): CandidateSummary[] {
  if (!session) return bridgeCandidates;
  const ids = new Set(session.candidateIds);
  return bridgeCandidates.filter((c) => ids.has(c.id));
}

export async function loadCurrentReviewSession(): Promise<CandidateReviewSession | null> {
  const stored = await chrome.storage.local.get(CURRENT_REVIEW_SESSION_KEY);
  return parseReviewSession(stored[CURRENT_REVIEW_SESSION_KEY]);
}

export type BeginReviewSessionParams = {
  captureId: string;
  source: ReviewCaptureSource;
  profileId: string;
  candidateIds: string[];
  capturedAt?: string;
  rawCaptureText?: string;
};

/** Replace the active review session (never append to the candidate list). */
export async function beginReviewSession(
  params: BeginReviewSessionParams,
): Promise<CandidateReviewSession> {
  const session: CandidateReviewSession = {
    captureId: params.captureId,
    source: params.source,
    capturedAt: params.capturedAt ?? new Date().toISOString(),
    profileId: params.profileId,
    candidateIds: [...params.candidateIds],
    rawCaptureText: (params.rawCaptureText ?? "").trim(),
  };
  const focusId = session.candidateIds[0] ?? null;
  await chrome.storage.local.set({
    [CURRENT_REVIEW_SESSION_KEY]: session,
    [CANDIDATES_TICK_KEY]: Date.now(),
    [CANDIDATES_FOCUS_KEY]: focusId,
  });
  return session;
}
