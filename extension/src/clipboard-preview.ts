/** Inspect clipboard / capture text before Capture (important_terms scope). */

export const IMPORTANT_TERMS_CLIPBOARD_WARN_THRESHOLD = 8;

export type ClipboardPreview = {
  charCount: number;
  lineCount: number;
  importantTermsCount: number;
  hasImportantTermsSection: boolean;
};

/** Count list entries under important_terms in raw YAML-ish text. */
export function countImportantTermsInCapture(text: string): number {
  const lines = text.split(/\r?\n/);
  let inSection = false;
  let count = 0;
  for (const line of lines) {
    if (/^\s*important_terms\s*:/i.test(line)) {
      inSection = true;
      continue;
    }
    if (inSection && /^\S/.test(line) && !/^\s*-\s+/.test(line)) {
      break;
    }
    if (inSection && /^\s*-\s+/.test(line)) {
      count += 1;
    }
  }
  return count;
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
