/** Inspect clipboard / capture text before Capture (important_terms scope). */

import type { ImportantTermsPreflightSummary } from "./types.js";

export const IMPORTANT_TERMS_CLIPBOARD_WARN_THRESHOLD = 8;

export type ClipboardPreview = {
  charCount: number;
  lineCount: number;
  importantTermsCount: number;
  hasImportantTermsSection: boolean;
};

function unquoteYamlListScalar(raw: string): string {
  const trimmed = raw.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"'))
    || (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

/** List item values under important_terms in raw YAML-ish text. */
export function parseImportantTermsInCapture(text: string): string[] {
  const lines = text.split(/\r?\n/);
  let inSection = false;
  const terms: string[] = [];
  for (const line of lines) {
    if (/^\s*important_terms\s*:/i.test(line)) {
      inSection = true;
      continue;
    }
    if (inSection && /^\S/.test(line) && !/^\s*-\s+/.test(line)) {
      break;
    }
    const match = line.match(/^\s*-\s+(.+?)\s*$/);
    if (inSection && match) {
      const value = unquoteYamlListScalar(match[1]);
      if (value) terms.push(value);
    }
  }
  return terms;
}

/** Count list entries under important_terms in raw YAML-ish text. */
export function countImportantTermsInCapture(text: string): number {
  return parseImportantTermsInCapture(text).length;
}

export function analyzeClipboardText(text: string): ClipboardPreview {
  const trimmed = text.trim();
  const lineCount = trimmed ? trimmed.split(/\r?\n/).length : 0;
  const importantTermsCount = countImportantTermsInCapture(trimmed);
  return {
    charCount: trimmed.length,
    lineCount,
    importantTermsCount,
    hasImportantTermsSection: /^\s*important_terms\s*:/im.test(trimmed),
  };
}

export function shouldConfirmLargeImportantTermsCapture(preview: ClipboardPreview): boolean {
  return preview.hasImportantTermsSection
    && preview.importantTermsCount > IMPORTANT_TERMS_CLIPBOARD_WARN_THRESHOLD;
}

export function buildLargeImportantTermsConfirmMessage(
  preview: ClipboardPreview,
  preflight: ImportantTermsPreflightSummary | null,
  translate: (key: string, params?: Record<string, string>) => string,
): string {
  if (preflight) {
    return translate("capture.clipboard_confirm_many_preflight", {
      total: String(preflight.total),
      existing: String(preflight.existing_count),
      added: String(preflight.added_count),
    });
  }
  return translate("capture.clipboard_confirm_many", {
    count: String(preview.importantTermsCount),
  });
}
