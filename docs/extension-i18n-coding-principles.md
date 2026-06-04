# Extension i18n Coding Principles

## Purpose

Sayane extension UI must work independently of the display language.

Japanese and English labels are presentation details. Business logic, Candidate classification, diff handling, approval rules, and safety checks must never depend on localized text.

This document defines coding principles for i18n-safe extension implementation.

## Core rule

Do not use visible UI strings as program state.

Use structured data, enum values, message keys, and API fields for logic. Use i18n only at the final rendering boundary.

Good:

```ts
const isRemovalCandidate =
  listDiff.operation === "list_remove" || listDiff.removed.length > 0;

label.textContent = t("review.list_diff_removed");
```

Bad:

```ts
const isRemovalCandidate = element.textContent?.includes("削除される重要語");
```

## Separation of concerns

Extension code should keep these layers separate:

1. Data semantics: structured values such as `rde_class`, `status`, `section`, `list_diff.removed`, `storagePolicy.targetPath`.
2. Decision logic: approve availability, Candidate classification, diff operation detection, merge policy checks.
3. Presentation: labels, help text, warnings, button text, tooltips.

Only the presentation layer should call `t(...)` for display text.

Decision logic should not inspect translated strings.

## Required patterns

### Use i18n keys for all user-visible text

All user-visible text in popup, side panel, options, warnings, dialogs, button labels, placeholders, and tooltips should be provided through i18n keys.

Preferred:

```ts
button.textContent = t("candidate.approve");
warning.textContent = t("review.persona_dump_warning");
```

Avoid:

```ts
button.textContent = "採用";
warning.textContent = "構造化されたペルソナ文書を検出しました。";
```

### Use structured fields for logic

Candidate logic should use fields such as:

- `candidate.status`
- `candidate.rde_class`
- `candidate.section`
- `candidate.evaluation_status`
- `detail.proposal.section`
- `diff.list_diff.added`
- `diff.list_diff.removed`
- `diff.list_diff.unchanged`
- `storagePolicy.promptExport`
- `storagePolicy.sensitivity`

Do not infer meaning from rendered text.

### Use explicit operation fields where possible

For list-style sections, prefer explicit operation fields from Bridge/API.

Recommended shape:

```ts
type ListDiffOperation =
  | "list_add"
  | "list_remove"
  | "list_replace"
  | "list_unchanged";
```

Then UI logic can use:

```ts
const isRemovalCandidate =
  listDiff.operation === "list_remove" ||
  listDiff.operation === "list_replace" ||
  listDiff.removed.length > 0;
```

The displayed label can then be localized separately:

```ts
label.textContent = t("review.list_diff_removed");
```

## Dialog and confirmation text

Confirmation dialogs must describe the operation without relying on language-specific parsing.

For example, clipboard `important_terms` preflight should use Bridge/API counts:

```ts
const message = t("capture.clipboard_confirm_terms_diff", {
  total: String(diff.total),
  existing: String(diff.existing),
  added: String(diff.added),
});
```

Do not parse the rendered confirmation text to decide what to do next.

## Approval and safety logic

Approve, reject, override, and merge availability must be based on structured state.

Examples of valid logic inputs:

- Candidate status: `pending`, `evaluated`, `approved`, `rejected`
- RDE category: `Preserved`, `Inferred Extension`, `Suspicious Drift`, etc.
- Section policy: blocked, unsupported, force-critical
- Explicit checkbox state and reason input values
- Bridge diff response

Invalid logic inputs:

- button text such as `採用`
- warning text such as `この評価結果では、そのまま採用できません`
- localized labels such as `保存された要素`
- DOM text such as `削除される重要語`

## Candidate Review requirements

Candidate Review must remain locale-independent.

Specific requirements:

- Review filters must use `ReviewFilterId` and `CandidateReviewClass`, not displayed labels.
- RDE labels must be rendered through `categoryLabel(...)` or i18n mapping, but logic must use raw category values.
- List removal detection must use `list_diff.removed.length > 0` or `list_diff.operation`, not localized section headers.
- Persona dump detection must use source text, section, and structured metadata, not warning text.
- Approve availability must use structured Candidate/detail/merge policy state, not button labels.

## Testing expectations

When adding UI behavior, include tests that prove logic is not tied to Japanese text.

Recommended tests:

- Run logic with Japanese and English locale and expect the same decision result.
- Verify that changing translation text does not change Candidate classification.
- Test list diff behavior using `list_diff.removed`, not label text.
- Test fallback behavior when translation keys are missing.

## Review checklist

Before merging extension UI changes, check:

- Are all user-visible strings behind i18n keys?
- Does any logic inspect `textContent`, labels, or translated strings?
- Are DOM queries based on stable class/data attributes rather than displayed text?
- Are operation types represented structurally?
- Are Japanese labels only presentation, never state?
- Are English and Japanese locales both supported for new keys?

## Design note

Sayane compares captured content against Sayane stored context, not LLM memory.

This boundary must remain clear across all locales. Localized text can explain the boundary, but the underlying state and decision logic must be language-independent.
