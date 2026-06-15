# ADR 0006: Post-Split Dependency Boundary Audit

## Status

Proposed

## Date

2026-06-15

## Context

ADR 0004 completed the Python responsibility split for Sayane.

The refactor reduced large responsibility-collapsed modules across CLI, Bridge, capture parsing, export, and candidate APIs. The final verification result was:

```text
621 passed, 16 warnings in 7.90s
```

The remaining warnings are known `PytestCollectionWarning` warnings and do not indicate test failures.

ADR 0004 addressed one class of architectural risk: Python modules growing into large files where responsibilities become difficult to inspect, test, and maintain.

However, after a large responsibility split, complexity can move from file size into dependency shape.

A codebase can appear cleaner because files are smaller while still becoming fragile through:

- import cycles
- reverse dependencies
- domain logic depending on transport layers
- usecases depending on Bridge routes
- facades accumulating behavior again
- compatibility aliases becoming permanent without review
- extension hooks relying on implicit module rebinding
- test-only assumptions leaking into production architecture

Sayane has a specific reason to care about this. The system handles Profile, Candidate, lineage, capture, export, and context portability. These are not just technical objects. They are mechanisms for preserving and reviewing human context.

Therefore, architectural responsibility collapse can become meaning-level collapse.

ADR 0006 extends ADR 0004 from file-level responsibility governance to graph-level dependency boundary governance.

## Decision

Sayane will introduce a post-split dependency boundary audit.

The first version of this audit will be informational only.

It will observe and report dependency-boundary risks, but it will not fail CI by default.

The audit should report:

1. import cycles
2. suspicious layer direction imports
3. facade growth after split
4. compatibility alias inventory
5. extension hook boundary risks
6. complexity concentration after split

Strict enforcement may be introduced later, but only after the audit rules have been exercised, reviewed, and accepted.

## Initial Audit Levels

The audit will have three conceptual levels.

### Level 1: Observation

Observation records architectural facts.

Examples:

- files scanned
- imports found
- modules per layer
- facade file sizes
- compatibility alias locations
- potential import cycles

Observation never implies failure.

### Level 2: Warning

Warning reports suspicious patterns that should be inspected by a human.

Examples:

- `domain` imports `bridge`
- `usecases` imports `bridge.routes`
- `evaluators` imports `cli`
- facade exceeds warning threshold
- compatibility alias remains
- hook wrapper lacks idempotence marker

Warnings are visible but non-blocking.

### Level 3: Enforcement

Enforcement may fail CI.

This level is explicitly out of scope for the first version.

Potential future enforcement targets include:

- import cycles
- `domain` importing CLI or Bridge
- `usecases` importing Bridge routes
- repeated hook wrapping
- export contract changes without golden test updates

Any move to enforcement requires a separate follow-up decision.

## Initial Layer Model

The first audit will use an approximate path-based layer model.

```text
src/sayane/cli/                 -> cli
src/sayane/bridge/routes/       -> bridge_routes
src/sayane/bridge/              -> bridge
src/sayane/usecases/            -> usecases
src/sayane/domain/              -> domain
src/sayane/core/                -> core
src/sayane/evaluators/          -> evaluators
src/sayane/vault/               -> vault
src/sayane/storage/             -> storage
src/sayane/mcp/                 -> mcp
```

The model is intentionally approximate in the first version.

It may be refined after several audit runs.

## Intended Dependency Direction

The intended high-level dependency direction is:

```text
entrypoints
  -> usecases
    -> domain / core / evaluators
      -> storage / vault / utilities
```

Where entrypoints include:

```text
cli
bridge
bridge_routes
mcp
future_gui
```

This is not intended as a rigid Clean Architecture purity rule.

Some shared utilities and core functions may be used across layers. However, domain logic should not depend on transport, presentation, or runtime entrypoint concerns.

## Suspicious Dependency Rules

The first audit should warn on the following import directions.

```text
domain -> cli
domain -> bridge
domain -> bridge_routes

core -> cli
core -> bridge_routes

evaluators -> cli
evaluators -> bridge_routes

usecases -> cli
usecases -> bridge_routes

bridge_routes -> cli
```

These warnings do not automatically prove a bug.

They indicate that the dependency should be inspected.

## Facade Watchlist

ADR 0004 intentionally preserved several compatibility facades.

These modules should remain thin:

```text
src/sayane/cli/app.py
src/sayane/bridge/app.py
src/sayane/core/export.py
src/sayane/evaluators/capture_parse.py
src/sayane/bridge/candidate_api.py
```

Initial warning thresholds:

```text
src/sayane/cli/app.py                  200 lines
src/sayane/bridge/app.py               200 lines
src/sayane/core/export.py              200 lines
src/sayane/evaluators/capture_parse.py 200 lines
src/sayane/bridge/candidate_api.py     300 lines
```

These thresholds are drift indicators, not architectural law.

A threshold warning should not fail CI in the first version.

## Compatibility Alias Inventory

The audit should track compatibility aliases preserved during ADR 0004.

Known aliases:

```text
_source_excerpt
_capture_preview_text
_candidate_summary
```

The report should include:

- alias name
- file path
- line number if available
- whether the alias appears in tests, if practical

The first audit must not recommend automatic removal.

Compatibility aliases are not inherently bad. They are technical memory. The risk is that they become undocumented permanent architecture.

## Export Contract Sensitivity

Export behavior is part of Sayane's context portability.

The dependency audit does not validate export semantics directly. Golden export tests remain responsible for output contract validation.

However, the audit should warn if export modules become coupled to transport or presentation layers.

Risk examples:

```text
core/export.py -> bridge/routes/context_export.py
core/export_yaml.py -> cli/commands/export.py
core/export_markdown_sections.py -> bridge/candidate_presenter.py
```

These patterns would indicate that portable context rendering is becoming coupled to delivery mechanisms.

## Candidate Lifecycle Sensitivity

Candidate behavior is central to Sayane.

The audit should watch for boundary erosion between:

- candidate policy
- candidate lifecycle
- candidate revision
- candidate lineage
- candidate presentation
- Bridge route handling

Risk examples:

```text
domain/candidate_policy.py -> bridge/candidate_presenter.py
usecases/candidate_lifecycle.py -> bridge/routes/candidates.py
bridge/routes/candidates.py contains approve/reject policy directly
```

The first audit may only detect import direction.

Later versions may add route-module size warnings or function-count warnings.

## sayane-pro Hook Boundary Sensitivity

`sayane-pro` may extend OSS Sayane behavior through hooks.

ADR 0004 exposed a semantic diff hook recursion issue in `sayane-pro`, where the semantic hook indirectly called the hook-installed function again.

The problematic shape was:

```text
hooked_function
  -> semantic_extension
    -> imported_hooked_function
      -> hooked_function
```

The preferred shape is:

```text
hooked_function
  -> semantic_extension(base_function=original_function)
    -> base_function
```

The OSS Sayane dependency audit must not require `sayane-pro`.

However, ADR 0006 records the extension boundary rule:

- capture the OSS base implementation before installing a hook
- make hook installation idempotent
- mark wrapped functions to avoid double wrapping
- pass base implementation explicitly when a semantic extension calls back into OSS behavior
- do not import a hook-mutated function as if it were the base implementation

`sayane-pro` should maintain separate regression tests for this boundary.

## Initial Implementation Strategy

The first implementation should prefer a lightweight script:

```text
tools/dependency_audit.py
```

The first version should use the Python standard library only unless a stronger need appears.

Suggested modules:

```text
ast
argparse
pathlib
collections
dataclasses
typing
```

The script should:

1. collect Python files under `src/sayane`
2. parse each file with `ast`
3. extract `import` and `from ... import ...`
4. resolve imports beginning with `sayane.`
5. map importer path to layer
6. map imported module to approximate layer
7. emit warnings for suspicious dependency pairs
8. check facade file line counts
9. search known compatibility aliases
10. produce text and Markdown reports
11. exit `0` by default even when warnings are present

## CI Policy

The initial CI behavior must be informational.

Recommended behavior:

```bash
python tools/dependency_audit.py \
  --format markdown \
  --output dependency-audit.md
```

CI should then:

- upload `dependency-audit.md` as an artifact
- append the report to `$GITHUB_STEP_SUMMARY`
- avoid failing CI because of warnings

The audit should fail only for execution errors, such as invalid arguments or unreadable paths.

Dependency warnings are not failures in the first version.

## Non-goals

The first version of ADR 0006 does not:

- enforce CI failures
- remove compatibility aliases
- refactor modules
- require visual graph rendering
- require `sayane-pro`
- validate export golden output
- enforce full Clean Architecture purity
- treat every reverse import as a bug

The first purpose is visibility, not punishment.

## Consequences

### Positive

- dependency drift becomes visible
- import cycles can be detected earlier
- post-split facade regression can be observed
- compatibility aliases become explicit
- future CI gates can be based on evidence
- pro extension boundaries are documented
- ADR 0004 becomes a continuing architectural practice rather than a one-time cleanup

### Negative

- introduces one more audit artifact to maintain
- may initially produce noisy warnings
- path-based layer mapping may be approximate
- developers may need to learn which warnings matter
- enforcement must be delayed until rules stabilize

## Alternatives Considered

### Do nothing

This would keep ADR 0004 as a one-time refactor.

Rejected because split modules can still develop hidden dependency collapse.

### Use import-linter immediately

`import-linter` is suitable for enforcing layer contracts.

Deferred because the dependency rules are not yet stable enough to enforce.

### Use grimp immediately

`grimp` may provide more accurate import graph inspection.

Deferred as a possible later improvement. The first version can start with a lightweight standard-library script.

### Fail CI immediately on violations

Rejected for the first version.

Premature enforcement could block development before the boundary rules are validated.

## Follow-up Tasks

- Add `tools/dependency_audit.py`.
- Add text and Markdown report output.
- Add non-blocking CI artifact job.
- Review several reports before enabling strict checks.
- Add `sayane-pro` hook boundary regression tests.
- Review compatibility aliases after the next release.
- Consider `grimp` or `import-linter` after rules stabilize.

## RDE Delta-M Review

### Preserved

ADR 0004's original goal is preserved: prevent responsibility collapse in Python modules.

Public API compatibility, export contracts, candidate API compatibility, and capture parser compatibility remain respected.

### Transformed

The concern shifts from file size to dependency shape.

This is a natural continuation of ADR 0004 rather than a contradiction.

### Added

ADR 0006 adds continuous observability, CI artifact reporting, compatibility alias inventory, and extension hook boundary awareness.

### Unresolved

The exact enforcement rules are not yet finalized.

The first version intentionally remains informational.

### Deviation Risk

The main risk is turning ADR 0006 into premature architectural policing.

A second risk is reducing ADR 0006 to another line-count check. File size is only one drift signal; the deeper concern is dependency-boundary collapse.

### Next Policy

Start with observation.

Move to warning.

Enforce only after repeated evidence and explicit decision.
