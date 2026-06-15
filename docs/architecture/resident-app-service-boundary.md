# Resident App Service Boundary

This document records ADR 0007 Phase 4 resident service preparation.

## Status

Initial service boundary is implemented.

This is not yet a production resident daemon.

It is a narrow application service seam that future CLI, Bridge, MCP, UI, and clipboard capture flows can share.

## Files

```text
src/sayane/app/capabilities.py
src/sayane/app/service.py
tests/test_resident_app_service.py
```

## Boundary

The resident app service follows this shape:

```text
future UI / clipboard capture / local service command
  -> ResidentAppService
    -> capability check
    -> existing capture/usecase path
    -> CandidateRepository
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

## Repository Diagnostics

`ResidentAppService.repository_counts()` requires `admin`.

It returns only non-secret counts:

```text
profile_id
candidate_count
review_decision_count
lineage_count
```

It must not expose candidate content, review reasons, plaintext vault data, or profile context payloads.

## Current Non-goals

The Phase 4 seam does not yet provide:

- `sayane app serve`
- daemon install/uninstall
- OS service integration
- persistent resident runtime selection
- production local auth tokens
- system tray UI
- Bridge route rewiring
- MCP runtime binding

## Next Step

A later phase should add an explicit resident runtime builder and command wiring:

```text
sayane app serve
  -> resident runtime builder
  -> repository bundle
  -> capability issuer
  -> local UI/Bridge/MCP adapters
```

The resident runtime should reuse repository/usecase boundaries rather than creating independent in-memory stores.
