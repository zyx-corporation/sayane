# Resident Runtime Selection

This document records the #184 production resident runtime selection boundary.

## Status

Initial runtime selection policy is implemented.

This is not a production daemon implementation. It is a narrow selection seam that decides how a `ResidentRuntime` obtains its `RepositoryBundle` without allowing CLI, UI, Bridge, or MCP entrypoints to import concrete storage backends directly.

## Files

```text
src/sayane/app/runtime.py
src/sayane/app/__init__.py
src/sayane/cli/commands/app.py
tests/test_resident_runtime.py
docs/architecture/resident-runtime-selection.md
```

## Dependency Direction

Allowed direction:

```text
CLI / UI / Bridge / MCP
  -> ResidentRuntime / ResidentAppService
  -> RepositoryBundle
  -> storage implementation
```

Disallowed direction:

```text
CLI / UI / Bridge / MCP
  -> SQLite runtime / vault adapter directly
```

The runtime boundary may select a backend and return a repository bundle. Entry points must consume the runtime/service abstraction instead of constructing storage implementations.

## Selection API

`build_resident_runtime()` now accepts explicit repository selection parameters:

```python
build_resident_runtime(
    repository_backend=...,
    repositories=...,
    vault_path=...,
    allow_test_vault=...,
)
```

The lower-level resolver is:

```python
select_resident_repositories(...)
```

It returns `ResidentRepositorySelection`, which contains non-sensitive metadata:

```text
backend
has_repositories
storage_boundary
notes
```

`ResidentRuntime.describe()` includes this metadata in diagnostic output.

## Backend Policy

### `legacy_process_local`

Default compatibility mode.

It does not install a durable repository bundle and is explicitly marked as not being a production durable resident state store.

This preserves existing command behavior while making the limitation visible.

### `injected_repository_bundle`

Used when a caller supplies an explicit `RepositoryBundle`.

This is the stable production-facing seam: future filesystem, SQLite, pro, or external backends should all converge into a repository bundle before reaching app services or entrypoints.

### `sqlite_test_local_vault`

Explicit test-only Local Vault selection.

It requires both:

```text
vault_path
allow_test_vault=True
```

This prevents the current SQLite test runtime from silently becoming production auth, production keychain integration, or durable credential storage.

### `future_pro_backend`

Reserved.

It intentionally raises `NotImplementedError` until a future backend can produce a `RepositoryBundle` through a reviewed boundary.

## Resident Serve Interaction

`sayane app serve` remains a delegation plan:

```text
sayane app serve --host 127.0.0.1 --port 38741
  -> sayane serve --host 127.0.0.1 --port 38741
```

The command does not start a second resident daemon and does not create another state universe.

The JSON plan now includes:

```text
repository_backend
storage_boundary
```

## Safety Properties

The #184 implementation fixes these properties:

- repository backend selection is centralized in `sayane.app.runtime`
- CLI does not import SQLite runtime or Local Vault adapter builders
- test-only SQLite Local Vault selection is explicit and guarded
- future pro backend support must pass through the `RepositoryBundle` seam
- runtime diagnostics expose backend class without exposing vault content, candidate text, review reasons, or profile context payloads

## Non-goals

This work does not implement:

- long-running daemon lifecycle
- OS service installation
- socket activation
- production local credential implementation
- token persistence
- network authentication
- pro backend storage
- migration framework

## RDE Delta-M Review

### Preserved

Resident App remains a coordination layer over shared repository/usecase boundaries.

Candidate, ReviewDecision, and Lineage state remain behind repositories rather than becoming direct CLI or UI state.

`sayane app serve` still avoids becoming a second resident server.

### Transformed

The previous runtime builder was only an assembly helper. It now also exposes a small but explicit repository selection policy.

### Supplemented

Runtime diagnostics now reveal which repository backend was selected and which storage boundary is active.

A test-only SQLite Local Vault path exists for runtime selection tests, but it is guarded so it cannot be mistaken for production auth.

### Unresolved

Real production daemonization, OS keychain integration, durable token persistence, and future pro backend selection remain unresolved.

### Deviation Risk

The main risk is treating `sqlite_test_local_vault` as production-ready. It is not. It is a persistence seam test path.

Another risk is adding future CLI or UI convenience imports that bypass `ResidentRuntime`. Tests now guard against the immediate CLI bypass case, but ADR 0006-style dependency audit should eventually watch this more broadly.
