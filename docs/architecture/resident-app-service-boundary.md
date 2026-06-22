# Resident App Service Boundary

This document records ADR 0007 Phase 4 resident service preparation, #181 resident UI skeleton work, #183 capability issuer hardening, and #184 resident runtime selection.

## Status

Initial service boundary is implemented.

This is not yet a production resident daemon.

It is a narrow application service seam that CLI, Bridge, MCP, UI, and clipboard capture flows can share.

## Files

```text
src/sayane/app/capabilities.py
src/sayane/app/service.py
src/sayane/app/runtime.py
src/sayane/app/ui.py
src/sayane/cli/commands/app.py
tests/test_resident_app_service.py
tests/test_resident_app_cli.py
tests/test_resident_runtime.py
tests/test_resident_ui_skeleton.py
tests/test_resident_capability_issuer.py
docs/architecture/resident-runtime-selection.md
```

## Boundary

The resident app service follows this shape:

```text
future UI / clipboard capture / local service command
  -> ResidentAppService / ResidentRuntime / app UI usecases
    -> capability check
    -> existing capture/usecase path
    -> CandidateRepository / ReviewDecisionRepository
```

The service must not:

- write directly to profile context from clipboard capture
- bypass Candidate review
- own a separate process-local state universe
- import direct SQLite adapters
- become Bridge route logic

## Capabilities

The initial local capability vocabulary is:

```text
ui
capture
review
export
mcp
bridge
admin
```

`admin` implies all capabilities.

The current capability implementation is intentionally local-only. It is a boundary model, not the final production security implementation.

## Capability Issuer Boundary

`CapabilityIssuer` adds explicit issuance metadata before a production auth system exists.

```text
CapabilityIssuer.issue()
  -> CapabilityToken
    -> subject
    -> issuer
    -> purpose
    -> scopes
    -> issued_at
    -> expires_at
```

Capability checks fail when a token is expired.

Capture, UI, MCP, Bridge, and admin scopes remain separable.

`admin` remains an explicit all-capability override.

The issuer boundary is not:

- OS keychain integration
- OAuth
- external authentication
- network authentication
- durable credential storage

## Clipboard Capture

Clipboard capture is explicit user capture.

It enters Sayane as a pending Candidate:

```text
clipboard text
  -> ResidentAppService.capture_clipboard_as_candidate()
  -> create_from_capture()
  -> CandidateUpdate(status="pending")
  -> CandidateRepository.save(candidate)
```

This preserves the Candidate review boundary.

Clipboard capture must not directly mutate ProfileContextRepository or ProjectContextRepository.

## Resident Runtime

`ResidentRuntime` is a thin assembly and repository-selection boundary for app commands.

```text
build_resident_runtime()
  -> select_resident_repositories()
  -> BridgeConfig
  -> ResidentAppService
  -> local capability map
```

Repository backend selection is centralized in `sayane.app.runtime`.

Entry points such as CLI, future UI, Bridge, and MCP should not import concrete SQLite or future backend builders directly. They should consume `ResidentRuntime`, `ResidentAppService`, or app-layer usecases.

The current supported backend modes are:

```text
legacy_process_local
injected_repository_bundle
sqlite_test_local_vault
future_pro_backend
```

`legacy_process_local` is the compatibility default and is explicitly not a production durable resident state store.

`injected_repository_bundle` is the production-facing seam: future backend implementations should produce a `RepositoryBundle` before reaching app services.

`sqlite_test_local_vault` is guarded by `allow_test_vault=True` and exists only to test the SQLite Local Vault persistence seam.

`future_pro_backend` is reserved and intentionally unimplemented.

See also:

```text
docs/architecture/resident-runtime-selection.md
```

## Resident UI Skeleton

The minimal resident UI skeleton is implemented as app-layer usecases, not as a final GUI.

```text
build_review_queue()
  -> ui capability
  -> CandidateRepository.list()
  -> ReviewDecisionRepository.list()
  -> resident_review_queue payload
```

The review queue is a review surface. It is not an MCP context export path.

```text
build_mcp_preview()
  -> mcp capability
  -> ReviewDecisionRepository.list()
  -> build_compiled_context()
  -> resident_mcp_preview payload
```

The MCP preview is explicitly marked as derived context and not canonical profile state.

Pending Candidates without decisions are added to `blocked_candidates` with `pending_candidate` exposure.

Rejected Candidates remain blocked by the MCP exposure guard.

```text
build_daemon_overview_preview()
  -> ui capability
  -> daemon status + liveness + readiness + runtime-init preview
  -> cleanup/repair preview summaries
  -> resident_daemon_overview_preview payload
```

The daemon overview is an app-facing aggregate preview for future UI code.

It remains derived and non-mutating, and it does not prove process identity, daemon readiness, or
API readiness.

The same overview payload is now also exposed through the Bridge as:

```text
GET /app/daemon-overview
```

This gives future local UI code an HTTP entrypoint without bypassing the app-layer capability and
aggregation boundary.

An app-facing aggregate payload is also available:

```text
build_app_overview()
  -> runtime diagnostics
  -> UI-friendly summary
  -> resident_review_queue
  -> resident_mcp_preview
  -> resident_daemon_overview_preview
  -> resident_app_overview
```

Bridge now exposes that aggregate view as:

```text
GET /app/overview
```

## See also

```text
docs/architecture/resident-app-ui-integration-contract.md
docs/architecture/resident-app-ui-screen-map.md
docs/architecture/resident-app-bootstrap-ui.md
docs/release/v1.0.14-ui-implementation-task-breakdown.md
```

For UI handoff, an explicit contract payload is also available:

```text
build_app_contract()
  -> preferred_entrypoint
  -> read_surfaces
  -> write_surfaces
  -> recommended_flow
  -> resident_app_contract
```

Bridge exposes that contract as:

```text
GET /app/contract
```

Detailed UI integration mapping is recorded in:

```text
docs/architecture/resident-app-ui-integration-contract.md
```

The first app-facing write surface is now:

```text
POST /app/capture-clipboard
  -> capture capability
  -> ResidentAppService.capture_clipboard_as_candidate()
  -> pending Candidate payload
```

This keeps UI-side writes inside the candidate/review boundary instead of writing profile state
directly.

App-facing review actions are now also exposed through the Bridge:

```text
GET /app/candidates
GET /app/candidates/{id}
GET /app/candidates/{id}/diff
POST /app/candidates/{id}/evaluate
POST /app/candidates/{id}/revise
POST /app/candidates/{id}/approve
POST /app/candidates/{id}/reject
```

These surfaces keep the app inside the existing candidate evaluation and approval workflow instead
of introducing a parallel profile-mutation path.

## Local Bootstrap HTML UI

The current resident app phase also includes a local Bridge HTML bootstrap UI:

```text
GET /app/ui
GET /app/ui/candidates
GET /app/ui/candidates/{id}
GET /app/ui/candidates/{id}/diff
GET /app/ui/daemon
```

This HTML layer is a presentation seam over the existing app-facing resident surfaces.

It is not the final GUI framework and does not add a new mutation boundary.

The current bootstrap UI also includes:

- cookie-backed follow-up navigation after the initial bearer-authenticated entry
- redirect-based success notices
- redirect-based validation / transition error feedback

## Resident Serve Decision

For the initial command wiring, `sayane app serve` is not an independent daemon.

It is a delegation plan for the existing Bridge command:

```text
sayane app serve --host 127.0.0.1 --port 38741
  -> sayane serve --host 127.0.0.1 --port 38741
```

This preserves existing Bridge behavior and avoids a second resident server path before runtime selection is stable.

`app serve` is deliberately testable without starting a long-running server:

```text
sayane app serve --json
```

The command rejects non-localhost bind addresses.

The JSON plan now exposes non-sensitive runtime selection metadata:

```text
repository_backend
storage_boundary
```

## Repository Diagnostics

`ResidentAppService.repository_counts()` requires `admin`.

It returns only non-sensitive counts:

```text
profile_id
candidate_count
review_decision_count
lineage_count
```

It must not expose candidate content, review reasons, plaintext vault data, or profile context payloads.

## Current Non-goals

The current seam does not yet provide:

- daemon install/uninstall
- OS service integration
- production local credential implementation
- final GUI framework
- system tray UI
- Bridge route rewiring
- MCP runtime binding
- pro backend implementation
- durable token persistence

## Next Step

Later phases should decide real resident daemon lifecycle and production capability hardening:

```text
resident daemon lifecycle
  -> OS/service integration
  -> production capability issuer
  -> Bridge/MCP/UI runtime binding
```

The resident runtime should continue reusing repository/usecase boundaries rather than creating independent in-memory stores.
