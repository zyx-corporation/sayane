# Candidate Detail Surface T-RDE: 2026-07-01

## Scope

This T-RDE note reviews the native macOS Candidate Detail surface after the observed mismatch between:

- the intended detail-screen contract, and
- the current UI rendering that made the detail body appear to be "the clipboard content itself."

Relevant implementation surface:

- `macos/SayaneApp/Sources/SayaneApp/Views/QueueAndDetailView.swift`
- `macos/SayaneApp/Sources/SayaneApp/Services/AppModel.swift`
- `macos/SayaneApp/Sources/SayaneApp/Support/AppStrings.swift`

Relevant design references:

- `docs/release/v1.0.14-candidate-detail-diff-design-note.md`
- `docs/release/v1.0.14-candidate-detail-diff-implementation-skeleton.md`
- `docs/release/v1.0.14-clipboard-capture-entry-design-note.md`

## Intended Meaning

The detail screen is defined to render, in order:

1. detail summary
2. proposal payload
3. evaluation payload
4. action availability summary
5. content body
6. diff preview
7. lineage preview

The key semantic boundary is:

- `proposal` is the structured review target
- `evaluation` is the bounded assessment state
- `content` is supporting body text or source-derived text

Therefore, the detail screen must not visually collapse into "clipboard text viewer" when the review target is a structured candidate proposal or a revised candidate.

## Observed Drift

The current native detail screen showed:

- summary
- proposal / evaluation ordering drift
- action controls detached from the intended summary position
- `content`
- diff / lineage

but did not foreground `proposal` or `evaluation` as first-class sections.

For clipboard-origin or candidate-revision candidates, this changed the apparent meaning of the screen:

- the operator could read the screen as "raw captured text" rather than
- "reviewable candidate proposal plus optional source/body context"

This was especially visible for revised candidates where `source_type == candidate_revision`, because the visible body still looked like direct input text instead of a candidate proposal under review.

## T-RDE Assessment

### Preserved

- `GET /app/screen-state/candidates/{id}` remains the primary detail payload.
- `diff` and `lineage` remain bounded companion review aids.
- action availability continues to come from `allowed_actions`.

### Supplemented

- the previous UI gave `content` a highly readable body presentation
- this made the candidate easier to skim as prose

This is a useful presentation property, but only as a secondary view.

### Distorted

- the screen visually promoted `content` above `proposal`
- the operator-facing meaning drifted from "candidate detail" toward "captured text detail"
- the distinction between:
  - review target
  - source text
  - revised text
  became too weak

This is not only a visual preference issue. It changes what the user is likely to believe they are approving, rejecting, or revising.

## Risk

If left unchanged, the detail surface risks:

- treating raw or revised text as the primary review artifact
- obscuring the structured proposal payload
- weakening the review boundary between candidate creation and candidate decision
- making clipboard-origin candidates appear more "final" or "literal" than intended

## Repair Decision

Adopt the following rendering rule:

1. keep `ui_summary` as the top summary surface
2. render `proposal` as the first content section
3. render `evaluation` as a separate section when present
4. render `allowed_actions` as a compact action-availability summary before the body text
5. render `content` only after `proposal` / `evaluation` / action availability
6. label `content` according to source semantics:
   - `clipboard` -> `取り込みテキスト`
   - `candidate_revision` / `user_revision` -> `修正文`
   - fallback -> `候補詳細`
7. keep copy/export text aligned with the same semantic ordering

## Classification

Recommended T-RDE classification:

- `Preserved`: detail payload contract, diff/lineage boundary, action boundary
- `Supplemented`: readable prose presentation of body text
- `Distorted`: candidate-detail meaning collapsed toward source/body text

Overall disposition:

```text
repair required
```

## Acceptance Criteria

- proposal content appears before raw/source body text
- evaluation content appears as its own section when available
- action availability appears before body text and stays bounded to `allowed_actions`
- content heading reflects source semantics rather than assuming all detail is clipboard text
- copy actions preserve the same semantic order
- the UI no longer implies that `content` alone is the review target

## Non-Goals

This repair does not:

- change Bridge payload shape
- change candidate review semantics
- change approve/reject/revise policy
- change diff/lineage endpoint responsibility
- redefine clipboard capture as direct profile mutation

## Conclusion

This change should be treated as a semantic-boundary repair, not mere UI polish.

The implementation should preserve the readable body text, but subordinate it to the structured
candidate proposal that the operator is actually reviewing.
