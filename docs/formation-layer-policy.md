# Formation-Layer Ethics and Export Policy

## Status

Proposed (vNext)

## Purpose

Define the ethics and export policy for formation-layer context in Sayane.

Formation-layer context includes personal development history, cognitive style, health-related influence patterns, and other information that can strongly improve assistant behavior but may be highly sensitive.

## Policy Layers

Formation-layer context is divided into three policy layers:

### 1. `private_raw` — Concrete Private Facts

Concrete, identifiable personal facts.

Examples:
- medical diagnoses
- family relationship details
- address-level life history
- raw childhood history
- financial status details

Default export policy:

```ts
promptExport: "never"
sensitivity: "sensitive"
```

These facts must never appear in prompt output, markdown bundles, or cross-LLM transfer unless explicitly released by the user for a specific session.

### 2. `abstracted_effect` — Abstracted Interaction Patterns

Abstracted, non-identifiable effects relevant to assistant interaction.

Examples:
- "user benefits from low-pressure reasoning space"
- "user prefers explicit uncertainty over confident unsupported claims"
- "user needs sufficient processing time before committing to answers"

Default export policy:

```ts
promptExport: "on_demand"
sensitivity: "internal"
```

These may be included in export bundles when the `formation` scope is explicitly requested. They carry no identifiable private facts.

### 3. `session_consent` — Session-Scoped Release

Temporary release of specific formation-layer context for a single session.

Rules:
- Must be explicitly enabled per session
- Must not be persisted in export bundles
- Must not leak into general context
- Should carry a timestamp and optional expiry

Default export policy:

```ts
promptExport: "on_demand"  // only with active session consent
sensitivity: "private"
```

## Export Rules

### Scope-based filtering

| Layer | `--scope formation` | `--scope identity,...` | No scope |
|---|---|---|---|
| private_raw | **Never** | **Never** | **Never** |
| abstracted_effect | Included | Excluded | Excluded |
| session_consent | Only with active consent | Excluded | Excluded |

### Policy enforcement

Export functions must:

1. Never include `private_raw` layer context in any export format (yaml/markdown/prompt).
2. Only include `abstracted_effect` when `formation` scope is explicitly requested.
3. Only include `session_consent` context when an active session consent token is present.

### CLI behavior

```bash
# Formation scope excludes private_raw by default
sayane export --format markdown --scope formation

# To include abstracted_effect:
sayane export --format markdown --scope formation,identity
```

## Implementation Notes

- The `export.py` module should check for a `formation` section in profiles and filter accordingly.
- A future `session_consent` mechanism (e.g., `sayane session consent --scope formation`) can grant temporary export permission.
- This policy is compatible with the existing `CandidateStoragePolicy` and `PromptExportPolicy` types.

## Related

- ADR 0001: Context Portability Export/Import Strategy
- Issue #124: Structured Persona IR Import Flow
- Issue #141: Context export formats
