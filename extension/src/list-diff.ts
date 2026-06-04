/** List-section diff helpers for Candidate Review UI. */

import type { CandidateDetail, CandidateDiff, CandidateSummary } from "./types.js";

export type ListDiff = {
  added: string[];
  removed: string[];
  unchanged: string[];
  unchangedCount?: number;
  operation?: string;
};

export const LIST_DIFF_SECTIONS = [
  "important_terms",
  "tags",
  "keywords",
  "interests",
  "focus_terms",
] as const;

export function isListDiffSection(section: string): boolean {
  return (LIST_DIFF_SECTIONS as readonly string[]).includes(section);
}

export function diffStringList(existing: string[], proposed: string[]): ListDiff {
  const normalize = (s: string) => s.trim();
  const normKey = (s: string) => normalize(s).toLowerCase();

  const existingMap = new Map<string, string>();
  for (const v of existing) {
    const n = normalize(v);
    if (n) existingMap.set(normKey(n), n);
  }
  const proposedMap = new Map<string, string>();
  for (const v of proposed) {
    const n = normalize(v);
    if (n) proposedMap.set(normKey(n), n);
  }

  const added: string[] = [];
  const removed: string[] = [];
  const unchanged: string[] = [];

  for (const [key, value] of proposedMap) {
    if (existingMap.has(key)) unchanged.push(value);
    else added.push(value);
  }
  for (const [key, value] of existingMap) {
    if (!proposedMap.has(key)) removed.push(value);
  }

  added.sort((a, b) => a.localeCompare(b));
  removed.sort((a, b) => a.localeCompare(b));
  unchanged.sort((a, b) => a.localeCompare(b));

  return { added, removed, unchanged, unchangedCount: unchanged.length };
}

export function listDiffFromBridgeDiff(diff: CandidateDiff): ListDiff | null {
  const raw = diff.list_diff;
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  return {
    added: Array.isArray(o.added) ? o.added.map(String) : [],
    removed: Array.isArray(o.removed) ? o.removed.map(String) : [],
    unchanged: Array.isArray(o.unchanged) ? o.unchanged.map(String) : [],
    unchangedCount:
      typeof o.unchanged_count === "number"
        ? o.unchanged_count
        : Array.isArray(o.unchanged)
          ? o.unchanged.length
          : 0,
    operation: typeof o.operation === "string" ? o.operation : undefined,
  };
}

export { countImportantTermsInCapture } from "./clipboard-preview.js";

export function listDiffFromProposal(detail: CandidateDetail): ListDiff | null {
  if (!isListDiffSection(detail.proposal.section ?? "")) return null;
  const added = (detail.proposal.items ?? [])
    .map((item) => String(item.name ?? "").trim())
    .filter(Boolean);
  const unchanged = (detail.proposal.already_present ?? [])
    .map((item) => String(item.name ?? "").trim())
    .filter(Boolean);
  return {
    added,
    removed: [],
    unchanged,
    unchangedCount: unchanged.length,
    operation: added.length > 0 ? "list_add" : "list_unchanged",
  };
}

export function importantTermsCardSummary(c: CandidateSummary): string | null {
  if (c.section !== "important_terms") return null;
  const withSummary = c as CandidateSummary & { display_summary?: string | null };
  const summary = withSummary.display_summary?.trim() || c.content_preview?.trim();
  return summary || null;
}

export function proposalItemsForListSection(detail: CandidateDetail): Array<Record<string, unknown>> {
  if (!isListDiffSection(detail.proposal.section ?? "")) {
    return (detail.proposal.items ?? []) as Array<Record<string, unknown>>;
  }
  return (detail.proposal.items ?? []) as Array<Record<string, unknown>>;
}
