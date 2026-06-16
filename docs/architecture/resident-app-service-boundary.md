# Resident App Service Boundary

This document records ADR 0007 Phase 4 resident service preparation and #181 resident UI skeleton work.

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

The current token is intentionally simple and local-only. It is a boundary model, not the final security implementation.

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

`ResidentRuntime` is a thin assembly boundary for app commands.

```text
build_resident_runtime()
  -> BridgeConfig
  -> ResidentAppService
  -> local capability map
```

The runtime builder does not select direct SQLite adapters by itself.

Persistent repository bundles must be injected explicitly when selected by a higher-level runtime policy.

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

The Phase 4 seam does not yet provide:

- daemon install/uninstall
- OS service integration
- persistent resident runtime selection
- production local credential implementation
- final GUI framework
- system tray UI
- Bridge route rewiring
- MCP runtime binding

## Next Step

A later phase should decide production resident runtime selection:

```text
resident runtime policy
  -> repository bundle selection
  -> capability issuer
  -> local UI/Bridge/MCP adapters
```

The resident runtime should reuse repository/usecase boundaries rather than creating independent in-memory stores.
