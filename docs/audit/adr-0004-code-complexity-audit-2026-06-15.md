# ADR 0004 Code Complexity Audit: 2026-06-15

## Scope

This audit reviews the existing Python codebase against ADR 0004: Python Code Size and Complexity Management Criteria.

The audit focuses on responsibility boundaries, dependency direction, I/O mixing, testability, and code areas that are likely to become hard to review or refactor.

## High-Risk Findings

### 1. `src/sayane/cli/app.py` is a CLI god file candidate

`src/sayane/cli/app.py` builds the Typer app and also contains profile commands, core commands, capture, export, import, review, candidate, storage, and MCP command registration.

It mixes:

- CLI argument parsing.
- Environment variable inspection.
- YAML settings loading.
- File creation and profile initialization.
- Git auto-commit compatibility.
- Capture orchestration.
- Export formatting dispatch.
- Import bundle verification and candidate rendering.
- Review decision display and persistence.

ADR 0004 treats large `app.py` files as warning signs when they mix interface, usecase, I/O, formatting, and domain decisions.

### 2. `src/sayane/bridge/app.py` mixes HTTP routing and usecase orchestration

`src/sayane/bridge/app.py` constructs the FastAPI app, defines auth dependency, maps HTTP exceptions, loads profiles, handles export/import, candidate lifecycle endpoints, preflight, compile, lineage, and context packet routes.

The current file is still readable, but it is a convergence point for:

- HTTP endpoint definitions.
- Authentication checks.
- Error translation.
- Profile loading.
- Import bundle orchestration.
- Candidate operation dispatch.

ADR 0004 recommends separating interface adapters from usecase orchestration once endpoints grow.

### 3. `src/sayane/evaluators/capture_parse.py` now contains multiple parser responsibilities

`capture_parse.py` contains:

- YAML-like input detection.
- YAML syntax error detection.
- YAML parse fallback.
- Persona YAML classification.
- Important terms YAML classification.
- Important terms fragment extraction.
- Profile value indexing for already-present detection.

Recent CI recovery added fragment support, making this file a clear split candidate. The main concern is not current line count alone, but mixed reasons for change: YAML detection, persona classification, important terms list diff, and profile-index matching can change independently.

### 4. `src/sayane/core/export.py` mixes scope selection, noise filtering, and multiple renderers

`export.py` contains:

- Scope-to-section mapping.
- Export noise filtering.
- YAML export.
- Prompt export.
- Generic markdown export.
- ChatGPT refined markdown export.
- Rendering helpers for identity, interaction, values, policies, principles, execution context, projects, and important terms.

The file is not yet beyond ADR 0004 warning thresholds, but it has several reasons for change. Golden tests show that export output is a public contract. This suggests splitting renderer concerns carefully, without changing output.

### 5. `src/sayane/bridge/candidate_api.py` mixes API payload, usecase rules, revision creation, lineage, and UI preview

`candidate_api.py` currently handles:

- Candidate operation error payloads.
- Listing candidates.
- Candidate details.
- Evaluation and approval transition checks.
- Unsafe RDE approval policy.
- Critical section explicit confirmation checks.
- Rejection.
- Diff and lineage access.
- Candidate revision creation.
- Lineage event recording.
- UI preview generation.

ADR 0004 suggests separating API presentation from usecase rules and domain transition policy.

## Recommended Fix Plan

### Phase 1: Add complexity visibility without refactoring behavior

- Add a lightweight complexity inventory document or CI job that records large files and warning thresholds.
- Consider introducing `radon` reporting as informational first, not failing CI.
- Track warning files by reason for change, not only line count.

### Phase 2: Split CLI commands by command group

Refactor `src/sayane/cli/app.py` into command group modules:

```text
src/sayane/cli/app.py                  # app assembly only
src/sayane/cli/commands/profile.py
src/sayane/cli/commands/core.py
src/sayane/cli/commands/capture.py
src/sayane/cli/commands/export.py
src/sayane/cli/commands/import_bundle.py
src/sayane/cli/commands/review.py
src/sayane/cli/commands/candidate.py
src/sayane/cli/commands/storage.py
src/sayane/cli/commands/mcp.py
```

Keep CLI argument parsing in command modules. Move reusable logic into usecase/service modules only when it is also used by Bridge/API.

### Phase 3: Split Bridge app routes from usecase behavior

Refactor `src/sayane/bridge/app.py` into route modules:

```text
src/sayane/bridge/app.py               # app factory and exception handlers
src/sayane/bridge/routes/profiles.py
src/sayane/bridge/routes/capture.py
src/sayane/bridge/routes/candidates.py
src/sayane/bridge/routes/export.py
src/sayane/bridge/routes/import_bundle.py
src/sayane/bridge/routes/lineage.py
src/sayane/bridge/routes/context_packet.py
```

Keep HTTP exception mapping at route level. Move reusable behavior to usecases.

### Phase 4: Split capture parsing responsibilities

Refactor `capture_parse.py` into:

```text
src/sayane/evaluators/capture_parse.py          # public facade
src/sayane/evaluators/yaml_detection.py
src/sayane/evaluators/persona_yaml_classifier.py
src/sayane/evaluators/important_terms_classifier.py
src/sayane/evaluators/important_terms_fragment.py
```

Keep the current public functions stable until tests are migrated.

### Phase 5: Split export renderers without changing golden output

Refactor `export.py` into:

```text
src/sayane/core/export.py               # public facade
src/sayane/core/export_scope.py
src/sayane/core/export_noise.py
src/sayane/core/export_yaml.py
src/sayane/core/export_prompt.py
src/sayane/core/export_markdown_generic.py
src/sayane/core/export_markdown_chatgpt.py
```

Golden fixtures must not change during the mechanical split. Behavior-changing export work should be a separate PR.

### Phase 6: Split candidate API presentation from lifecycle usecases

Refactor `candidate_api.py` into:

```text
src/sayane/bridge/candidate_api.py        # facade / HTTP-facing payload functions
src/sayane/usecases/candidate_lifecycle.py
src/sayane/usecases/candidate_revision.py
src/sayane/bridge/candidate_presenter.py
src/sayane/domain/candidate_policy.py
```

Move unsafe approval categories and transition policy out of Bridge API presentation code.

## Acceptance Criteria

- No behavior change in the first refactoring PRs.
- Golden export tests remain unchanged during mechanical split.
- CLI acceptance tests remain green.
- Bridge API tests remain green.
- Public import paths are preserved or explicitly deprecated.
- Each extracted module has a clear reason for change.
- Unit tests can target extracted pure functions without BridgeConfig, FastAPI, Typer, filesystem, or Git where possible.

## RDE Review

### Preserved elements

- Existing CLI behavior.
- Existing Bridge API behavior.
- Existing export output contracts.
- Existing candidate lifecycle semantics.
- Existing capture fragment compatibility.

### Transformed elements

The audit reframes code size as a semantic boundary issue:

```text
large file
↓
mixed reasons for change
↓
difficult tests and broad blast radius
↓
ΔM becomes harder to observe
```

### Unresolved elements

- Whether to make `radon` a hard CI gate or only an informational report.
- Whether candidate lifecycle policies should live under `domain/` or `usecases/`.
- Whether Bridge route modules should be routers or functions registered by `create_app()`.
- How aggressively to keep backward-compatible imports.

### Deviation risks

- Splitting files without clarifying semantic boundaries.
- Breaking CLI or Bridge behavior during a mechanical refactor.
- Updating golden outputs during a structural split.
- Moving side effects inward instead of outward.
- Creating too many tiny modules too early.

## Final Recommendation

Open one tracking issue for ADR 0004 refactoring, then perform small PRs in this order:

1. CLI command group split.
2. Bridge route split.
3. Capture parser split.
4. Export renderer split.
5. Candidate lifecycle / presenter split.
6. Optional complexity reporting in CI.

Do not combine these into one large refactor PR.
