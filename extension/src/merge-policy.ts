/**
 * Mirror of sayane.evaluators.sections merge policy for approve UI.
 */

const BLOCKED_SECTIONS = new Set(["identity.name", "identity.preferred_name"]);

const CRITICAL_ROOTS = new Set(["identity", "values", "policy", "voice"]);

/** Sections that require checkbox + adopt reason before approve (UI + Bridge). */
export const CRITICAL_CONTEXT_SECTIONS = new Set(["important_terms"]);

export function requiresExplicitContextConfirmation(section: string): boolean {
  return CRITICAL_CONTEXT_SECTIONS.has(section);
}

const FORCE_ALLOWED_SECTIONS = new Set([
  "values.core",
  "voice.tone",
  "policy.response.avoid",
  "policy.response.prefer",
  "identity.roles",
  "knowledge.concepts",
  "important_terms",
  "major_projects",
  "communication_mode",
]);

export function isCriticalSection(section: string): boolean {
  const root = section.split(".")[0] ?? "";
  return CRITICAL_ROOTS.has(root);
}

export function isBlockedMergeSection(section: string): boolean {
  return BLOCKED_SECTIONS.has(section);
}

/** Sections that may merge only with force_critical (matches Python can_merge_section). */
export function requiresForceCriticalMerge(section: string): boolean {
  if (isBlockedMergeSection(section)) return false;
  if (section === "knowledge.concepts") return false;
  if (FORCE_ALLOWED_SECTIONS.has(section)) return true;
  return isCriticalSection(section);
}

export function canMergeSection(section: string, forceCritical: boolean): boolean {
  if (isBlockedMergeSection(section)) return false;
  if (section === "knowledge.concepts") return true;
  if (forceCritical && FORCE_ALLOWED_SECTIONS.has(section)) return true;
  if (!isCriticalSection(section)) return true;
  return false;
}

/** Sections the Bridge can apply on approve (matches Python merge.py). */
const AUTO_MERGE_SECTIONS = new Set([
  "knowledge.concepts",
  "important_terms",
  "values.core",
  "voice.tone",
  "policy.response.avoid",
  "policy.response.prefer",
  "identity.roles",
  "major_projects",
  "communication_mode",
]);

export function isAutoMergeSupported(section: string): boolean {
  if (isBlockedMergeSection(section)) return false;
  return AUTO_MERGE_SECTIONS.has(section);
}
