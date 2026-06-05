# ADR 0001: Context Portability Export / Import Strategy

## Status

Proposed

## Date

2026-06-05

## Context

Sayane is moving from simple context capture toward a reviewable context portability system.

Recent vNext work added or advanced:

- Candidate Review in the side panel
- Structured Persona IR import
- edited Candidate creation
- important_terms add / remove handling
- Bridge preflight diff for important_terms
- i18n-safe extension coding principles
- lightweight lineage display and API work

The next Context Portability phase must support cross-LLM transfer without turning Sayane into a raw prompt dumping tool.

The main design tension is:

- users need portable context across ChatGPT, Claude, Gemini, DeepSeek, and local LLM UIs;
- different LLMs accept different prompt shapes and preserve different semantic structures;
- sensitive context, especially formation-layer context, is useful but should not be exported by default;
- imported context must not directly mutate the canonical profile without review.

Therefore, export/import must be treated as a controlled transformation pipeline rather than file copying.

## Decision

Sayane will treat Context Portability as a structured pipeline:

```text
Canonical Context / Profile IR
  → scoped export bundle
  → target adapter rendering
  → cross-LLM transfer test
  → receiving import bundle
  → Candidate Review
  → approved stored context
```

Export and import will follow these rules.

### 1. Export formats

Sayane should support multiple export formats:

- `yaml`: canonical machine-readable bundle
- `markdown`: human-readable and LLM-readable bundle
- `prompt`: compact prompt-oriented rendering for conversation injection

YAML is not assumed to be the best LLM input format. Markdown should be the first practical target for cross-LLM transfer testing.

### 2. Export scopes

Export must support explicit scopes.

Suggested scopes:

- `identity`
- `interaction`
- `writing`
- `technical`
- `projects`
- `ethics`
- `formation`
- `important_terms`

Scope selection must be explicit. Sensitive scopes must not be included by accident.

### 3. Target adapters

Export must support target adapters.

Suggested targets:

- `generic`
- `chatgpt`
- `claude`
- `gemini`
- `deepseek`
- `openwebui`

A target adapter may change formatting and ordering, but it must not invent new context. Any transformation must preserve the source bundle's meaning as much as possible.

### 4. Storage vs prompt export

Storing context and exporting context into LLM prompts are separate operations.

Profile IR entries may have export policy metadata such as:

```ts
export type PromptExportPolicy = "default" | "on_demand" | "never";
export type CandidateSensitivity = "public" | "internal" | "private" | "sensitive";
```

Sensitive or private entries may be stored in Sayane but excluded from normal prompt export.

### 5. Formation layer

Formation-layer context requires special policy.

Raw formation details should default to `promptExport: "never"` unless explicitly released for a session.

Portable formation context should prefer abstracted effects, not raw private facts.

Example:

```text
Prefer: "The user benefits from low-pressure, high-autonomy reasoning space."
Avoid default export: raw medical history, family details, address-level life history.
```

### 6. Import must go through Candidate Review

Importing a bundle must not directly merge into canonical context.

The import path should be:

```text
import bundle
  → Candidate generation
  → RDE evaluation / diff
  → approve / reject / edit
  → stored context
```

Conflicts should be represented as Candidates and lineage events, not hidden merge side effects.

### 7. Lineage

Export/import operations must preserve lineage.

At minimum, lineage should record:

- export source profile
- export format
- target adapter
- scope list
- import source
- generated Candidates
- approval decisions
- resulting context paths

Lineage is required to evaluate portability loss and responsibility.

### 8. RDE evaluation for portability

Cross-LLM transfer quality should be evaluated through RDE-style categories:

- preserved elements
- authorized transformations
- inferred extensions
- unresolved gaps
- suspicious drift
- critical distortion

The initial baseline target may use a composite score, but the practical output must include concrete loss/drift notes, not only a number.

## Consequences

### Positive

- Context portability becomes auditable.
- LLM-specific prompt formatting can improve transfer quality without changing canonical context.
- Sensitive context can remain stored but not exported by default.
- Imports remain reviewable and reversible.
- Cross-LLM experiments can produce useful RDE evidence.

### Negative / cost

- Export/import becomes more complex than a plain YAML copy.
- Bridge and CLI APIs must support scopes, formats, and adapters.
- Tests must cover multiple locales and targets.
- Formation-layer policy must be designed before broad export.

## Implementation Plan

1. Implement `export --format markdown`.
2. Add `export --scope` and `export --target` design.
3. Run a ChatGPT transfer baseline test.
4. Implement import-to-Candidate Review path.
5. Define formation-layer export ethics and policy.
6. Expand to round-trip and multi-LLM tests.

## Non-goals

- Raw persona prompt dumping
- Silent import merge
- Automatic self-profile optimization
- Exporting all stored context by default
- Treating one LLM's interpretation as canonical truth

## Related Issues

- #119 Edited Candidate creation flow
- #124 Structured Persona IR Import Flow
- #125 Lineage API and UI
- #127 important_terms preflight diff
- #132 important_terms removal workflow

Additional implementation issues should be created for export formats, cross-LLM tests, import-to-candidates, and formation-layer ethics.
