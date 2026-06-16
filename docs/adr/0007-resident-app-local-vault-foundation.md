# ADR 0007: Resident App and Local Vault Foundation

## Status

Proposed

## Date

2026-06-15

## Context

ADR 0004 split large Python responsibilities across CLI, Bridge, capture parsing, export, and candidate APIs.

ADR 0006 added an informational dependency-boundary audit so that the post-split codebase does not quietly regress into hidden import coupling or facade growth.

The next architectural risk is not only file size or dependency direction. It is runtime state fragmentation.

Sayane currently has several interaction surfaces:

- CLI
- Bridge API
- MCP exposure
- candidate review flows
- context export
- storage backends
- future resident app UI

If each surface owns its own in-memory state, review decisions and candidate lifecycle data can diverge across processes. That would weaken Sayane's central promise: context changes should remain inspectable, reviewable, and lineage-aware.

Issue #170 identifies this transition as the resident app and local vault foundation. It calls for repository contracts, persistent storage, local service boundaries, and avoidance of separate in-memory stores across processes.

This ADR records the architectural boundary before implementation begins.

## Decision

Sayane will move toward a resident local application architecture backed by a shared repository layer.

The repository layer will become the coordination point for durable candidate, review, lineage, profile, and project-context state.

CLI, Bridge, MCP, and future app UI should access shared state through explicit repository/usecase boundaries rather than each keeping independent process-local stores.

The initial implementation should remain conservative:

1. define repository contracts first
2. add in-memory implementations for tests only
3. add SQLite-backed MVP persistence after the contracts are stable
4. keep filesystem/Git compatibility where applicable
5. avoid introducing commercial-only dependencies into OSS Sayane
6. keep exposure policy centralized in the MCP exposure guard
7. keep review decisions durable enough to be reused across CLI, Bridge, MCP, and future resident UI
8. centralize resident repository backend selection behind the runtime boundary

## Architectural Boundary

The resident app foundation introduces a new responsibility boundary.

```text
entrypoints
  -> usecases / resident runtime
    -> repositories / domain / core
      -> storage backend / filesystem / sqlite adapter
```

Entrypoints include:

```text
cli
bridge
mcp
future_app_ui
future_clipboard_capture
```

Entrypoints must not become the owner of candidate lifecycle state.

They may initiate operations, display state, or call usecases, but durable state belongs behind repository contracts.

## Repository Contracts

The first repository contracts cover:

- CandidateRepository
- ReviewDecisionRepository
- LineageRepository
- ProfileContextRepository
- ProjectContextRepository
- RepositoryBundle

The exact Python module layout may evolve, but the intended ownership is:

```text
src/sayane/domain/      -> domain models and policies
src/sayane/usecases/    -> orchestration and application behavior
src/sayane/storage/     -> backend-neutral storage contracts and adapters
src/sayane/vault/       -> local vault and filesystem concerns
src/sayane/bridge/      -> transport and presentation boundary
src/sayane/mcp/         -> MCP exposure boundary
src/sayane/app/         -> resident service/runtime/usecase boundary
```

If a repository contract becomes too transport-aware, it should be moved or split.

If a Bridge route directly implements candidate approval policy, that is a boundary violation.

## Initial Repository Interface Direction

Repository methods should express domain operations, not UI events.

Preferred shape:

```text
save_candidate(candidate)
get_candidate(candidate_id)
list_candidates(filter)
save_review_decision(decision)
list_review_decisions(candidate_id=None)
append_lineage_event(event)
load_profile_context(scope)
save_profile_context(scope, context)
```

Avoid shapes such as:

```text
click_approve_button(...)
bridge_post_candidate(...)
render_review_card(...)
```

Those belong to presentation, route, or UI layers.

## Persistent Review Decisions

A specific early goal is to make `load_review_decisions()` persistent.

The behavior must not allow MCP compiled context to observe a different review-decision state from the one used by CLI or Bridge.

The intended flow is:

```text
Candidate created
  -> candidate repository stores proposal
  -> human review writes ReviewDecision
  -> lineage event records decision
  -> MCP compiled context reads durable review decisions
  -> exposure guard remains the final exposure policy engine
```

The MCP exposure guard must remain the only exposure policy engine.

Persistence should provide facts to the guard. It should not bypass or duplicate the guard.

## Local Vault and SQLite MVP

The first persistent backend may be SQLite.

However, SQLite should enter through an adapter boundary, not directly through CLI, Bridge, or MCP modules.

The initial SQLite MVP includes:

- SQLite-backed Local Vault schema/runtime
- repository implementation for candidates and review decisions through Vault stores
- tests proving persistence across process-like reloads
- no commercial-only encrypted backend dependency
- clear future path for keyring / encrypted-record design

The encrypted SQLite backend remains a likely commercial extension point in `sayane-pro`, while OSS Sayane keeps the repository and backend contracts stable.

## Resident App Service Boundary

The future resident service may be exposed as something like:

```bash
sayane app serve
```

or as an evolution of:

```bash
sayane serve
```

The exact command is not decided by this ADR.

This ADR only decides that a resident process must not create a second independent state universe.

The resident app service should route through shared usecases and repositories.

It may provide local capabilities for:

- clipboard capture
- candidate review
- context export
- profile/project context browsing
- Bridge-compatible API access
- MCP-compatible context serving

It must not bypass Candidate review boundaries.

## Resident Runtime Selection

Runtime selection is now an explicit resident app boundary.

```text
CLI / UI / Bridge / MCP
  -> ResidentRuntime / ResidentAppService
  -> RepositoryBundle
  -> storage implementation
```

CLI, UI, Bridge, and MCP must not construct SQLite Local Vault or future backend implementations directly.

The runtime selection vocabulary is:

```text
legacy_process_local
injected_repository_bundle
sqlite_test_local_vault
future_pro_backend
```

`legacy_process_local` preserves compatibility, but is not production durable resident state.

`injected_repository_bundle` is the stable production-facing seam.

`sqlite_test_local_vault` is an explicit test-only persistence seam and requires `allow_test_vault=True`.

`future_pro_backend` is reserved until a reviewed backend can produce a `RepositoryBundle` without leaking commercial/pro concerns into the OSS entrypoints.

## Capability and Local Token Direction

A resident app requires local capability boundaries.

The first version should distinguish at least:

```text
ui
capture
review
export
mcp
bridge
admin
```

The first implementation may use simple local-only tokens or capability stubs.

The important architectural rule is that capabilities should be explicit and testable before the app grows into a privileged local daemon.

## Clipboard Capture Direction

Issue #169 argues that full-page browser capture is noisy and less central, while explicit clipboard or selected-text capture remains valuable.

ADR 0007 is compatible with that direction.

Clipboard capture should enter Sayane as a Candidate through the same repository/usecase path as other capture sources.

It should not become a special path that writes directly to profile context.

```text
clipboard text
  -> capture parser
  -> Candidate
  -> review
  -> decision
  -> lineage
  -> profile/project context update
```

## Compatibility with Filesystem and Git Backends

The repository layer must not erase Sayane's filesystem/Git compatibility.

Filesystem-backed profile context and Markdown vault usage remain important for context portability.

The persistent repository layer is for durable application state and review coordination.

The local vault remains the human-readable and portable context substrate.

The implementation should avoid treating SQLite as the only source of meaning.

## Non-goals

ADR 0007 does not decide:

- final GUI technology
- final app packaging format
- final daemon command name
- encrypted SQLite schema
- commercial licensing behavior
- full sync/merge policy for Obsidian vaults
- automatic browser page capture restoration
- production resident daemon lifecycle
- production authentication or token persistence

ADR 0007 also does not require all persistence to be implemented in one step.

## Consequences

### Positive

- CLI, Bridge, MCP, and future UI can share durable review state
- candidate lifecycle becomes less process-local
- MCP compiled context can read real review decisions
- future resident app work has a stable boundary
- clipboard capture can replace noisy page capture without weakening review semantics
- sayane-pro can extend storage without owning the OSS contract
- resident runtime selection is auditable before daemonization

### Negative

- introduces a repository abstraction that must be maintained
- may increase short-term implementation complexity
- requires migration design before persistence is fully useful
- risks over-abstracting if contracts are created too broadly
- requires careful tests to avoid fake in-memory behavior being mistaken for production behavior
- requires future dependency audits to prevent entrypoints from bypassing runtime selection

## Implementation Plan

### Phase 1: Contracts and test providers

- Add repository contract module(s).
- Add test/in-memory providers for tests only.
- Keep production paths unchanged except where explicitly wired.
- Add contract tests for candidate and review-decision repositories.

### Phase 2: Persistent review decisions

- Implement persistent `load_review_decisions()` through the repository layer.
- Ensure MCP compiled context reads durable review decisions.
- Keep MCP exposure guard as the final policy engine.

### Phase 3: SQLite MVP

- Add migration skeleton.
- Add SQLite-backed CandidateRepository and ReviewDecisionRepository.
- Add reload/persistence tests.
- Keep filesystem/Git compatibility.

### Phase 4: Resident service preparation

- Define service/usecase boundary for a resident app.
- Ensure CLI and Bridge can share repository-backed state.
- Add local capability model stubs.
- Prepare clipboard capture as Candidate input.

### Phase 5: Resident command, UI, and capability preparation

- Add initial resident command wiring.
- Keep `sayane app serve` as a delegation plan to existing Bridge command.
- Add resident review queue and MCP preview skeleton.
- Add capability issuer metadata and expiry semantics.

### Phase 6: Runtime selection boundary

- Centralize repository backend selection in `sayane.app.runtime`.
- Keep direct SQLite/runtime imports out of CLI and presentation entrypoints.
- Add explicit backend metadata to resident diagnostics.
- Guard test-only SQLite Local Vault selection.
- Reserve future pro backend selection behind `RepositoryBundle`.

## Implementation Progress

### Completed: Phase 1

Implemented in:

```text
src/sayane/storage/repositories.py
tests/test_repository_contracts.py
docs/architecture/repository-boundary.md
```

Phase 1 adds repository contracts, explicit test-only in-memory providers, a test repository bundle, and compatibility tests proving that existing vault stores satisfy the repository contracts.

### Completed: Phase 2

Implemented in:

```text
src/sayane/core/review_decision.py
tests/test_review_decision_repository_seam.py
```

Phase 2 routes `save_decision()`, `list_decisions()`, `load_review_decisions()`, and `get_decisions_for_candidate()` through a configurable `ReviewDecisionRepository` seam while preserving the legacy in-memory fallback.

This lets MCP compiled context read repository-backed review decisions without moving the exposure policy out of `mcp_context.py`.

### Completed: Phase 3 MVP path

Implemented and documented in:

```text
src/sayane/vault/sqlite_runtime.py
tests/test_sqlite_vault_store.py
docs/architecture/sqlite-repository-mvp.md
```

Phase 3 uses the existing SQLite-backed Local Vault runtime. Tests prove repository reload, review decision persistence through SQLite-backed vault stores, `save_decision()` write-through via the repository seam, and MCP compiled context consumption of SQLite-backed review decisions.

### Completed: Phase 4 service seam

Implemented and documented in:

```text
src/sayane/app/capabilities.py
src/sayane/app/service.py
tests/test_resident_app_service.py
docs/architecture/resident-app-service-boundary.md
```

Phase 4 adds a resident app service boundary, local capability model, repository diagnostics, and clipboard capture as Candidate input.

The service seam prepares future resident runtime wiring without adding a production daemon command yet.

### Completed: Phase 5 resident command/UI/capability preparation

Implemented and documented in:

```text
src/sayane/app/runtime.py
src/sayane/app/ui.py
src/sayane/cli/commands/app.py
tests/test_resident_runtime.py
tests/test_resident_ui_skeleton.py
tests/test_resident_capability_issuer.py
docs/architecture/resident-app-service-boundary.md
```

Phase 5 adds initial resident runtime command wiring, `sayane app serve` delegation, resident UI review queue/MCP preview skeleton, and capability issuer hardening.

### Completed: Phase 6 runtime selection boundary

Implemented and documented in:

```text
src/sayane/app/runtime.py
src/sayane/app/__init__.py
src/sayane/cli/commands/app.py
tests/test_resident_runtime.py
docs/architecture/resident-runtime-selection.md
```

Phase 6 centralizes resident repository selection behind the runtime boundary. It keeps the default compatibility path visible as `legacy_process_local`, supports explicit injected repository bundles, guards test-only SQLite Local Vault selection, and reserves future pro backend selection behind the `RepositoryBundle` seam.

## Test Policy

Initial tests should prove:

- repository contracts can store and load candidates
- repository contracts can store and load review decisions
- `load_review_decisions()` can be backed by persistent state
- MCP compiled context reads the same durable review decisions
- in-memory providers are limited to tests or explicit dev fixtures
- Bridge routes do not directly own approval policy
- clipboard capture proposals still enter as Candidates
- resident runtime selection exposes non-sensitive backend metadata
- CLI does not directly import SQLite Local Vault runtime builders

## Dependency Audit Interaction

ADR 0006 should be updated later to watch the new repository boundary.

Potential future warnings:

```text
bridge_routes -> sqlite_adapter
mcp -> sqlite_adapter
cli -> sqlite_adapter
cli -> sqlite_runtime
future_ui -> sqlite_runtime
domain -> repository implementation
repository contracts -> bridge_routes
resident service -> direct sqlite3
clipboard capture -> profile context direct write
```

Repository contracts may be imported by usecases.

Repository implementations should stay below usecases and entrypoints.

## RDE Delta-M Review

### Preserved

Sayane's Candidate review boundary, lineage orientation, context portability, filesystem/Git compatibility, and MCP exposure guard remain central.

### Transformed

The main architectural concern shifts from post-split dependency visibility to runtime state coherence.

CLI, Bridge, MCP, and future UI stop being independent process-local islands and begin converging on shared repository-backed state.

The resident runtime builder transforms from a thin command assembly helper into a narrow repository selection boundary.

### Added

ADR 0007 adds repository contracts, persistent review decision direction, resident app service boundary, local capability direction, clipboard-capture alignment, resident UI skeletons, capability issuer metadata, and explicit runtime backend selection.

### Unresolved

The production daemon lifecycle, OS/service integration, production capability implementation, durable token persistence, Bridge/MCP runtime rebinding, and future pro backend implementation remain unresolved.

Encrypted local storage is acknowledged but not specified here.

### Deviation Risk

The main risk is creating a repository abstraction that is too broad before real usecases prove the shape.

A second risk is treating SQLite as the meaning source and forgetting that the human-readable local vault remains Sayane's context substrate.

A third risk is letting the resident service become a privileged shortcut around Candidate review.

A fourth risk is mistaking `sqlite_test_local_vault` for a production resident backend. It is only an explicit persistence seam test path.

### Update Policy

ADR 0007 should be revised again when a real resident daemon lifecycle, production credential model, or Bridge/MCP runtime binding is implemented.
