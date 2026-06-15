# Repository Boundary

This document records the initial repository boundary introduced by ADR 0007.

## Purpose

Sayane has multiple runtime entrypoints:

- CLI
- Bridge API
- MCP
- future resident app UI
- future clipboard capture

These entrypoints must not each own independent process-local state for Candidate, ReviewDecision, Lineage, or context data.

The repository boundary provides a shared contract for durable application state.

## Layer Direction

```text
entrypoints
  -> usecases
    -> repository contracts
      -> repository implementations
        -> storage backend / vault / sqlite
```

Entrypoints may call usecases.

Usecases may depend on repository contracts.

Repository implementations may depend on storage backends.

Repository contracts must not depend on Bridge routes, CLI commands, MCP handlers, or UI presentation.

## Initial Contracts

The Phase 1 contracts are defined in:

```text
src/sayane/storage/repositories.py
```

They include:

- `CandidateRepository`
- `ReviewDecisionRepository`
- `LineageRepository`
- `ProfileContextRepository`
- `ProjectContextRepository`
- `RepositoryBundle`

## Test-only Providers

Phase 1 includes explicit test-only in-memory providers.

These providers are useful for contract tests and future usecase tests.

They must not become the production resident app state store.

Production code should use a real vault-backed or future SQLite-backed repository bundle.

## Existing Vault Stores

The existing vault-backed stores are already close to the ADR 0007 repository boundary:

- `VaultCandidateStore`
- `VaultReviewDecisionStore`
- `VaultLineageStore`
- `VaultRepositoryBundle`

Phase 1 does not replace them.

Instead, tests verify that they satisfy the new repository contracts.

## Review Decision Persistence Direction

The next phase should route `load_review_decisions()` through a repository-backed path.

The important constraint is:

```text
persistence supplies review facts
MCP exposure guard decides exposure
```

Repository persistence must not bypass or duplicate the MCP exposure guard.

## Do Not Do This

Avoid direct dependencies such as:

```text
bridge_routes -> sqlite_adapter
mcp -> sqlite_adapter
cli -> sqlite_adapter
domain -> repository implementation
repository contracts -> bridge routes
```

Avoid treating SQLite as the meaning source.

The local vault remains the human-readable context substrate.

Repositories coordinate durable application state.
