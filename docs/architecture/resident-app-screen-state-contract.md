# Resident App Screen State Contract

Status: framework_neutral_screen_state_mvp

## Goal

This document records the current framework-neutral screen state builders for the resident app.

They exist to help a future GUI implementation reuse stable app-layer view models instead of
re-deriving screen state separately inside a specific frontend framework.

## Current builders

The current app layer provides:

```text
build_home_screen_state(overview)
build_candidate_queue_screen_state(queue_payload)
build_candidate_detail_screen_state(detail_payload)
build_daemon_panel_screen_state(daemon_payload)
```

## Purpose

These builders turn current app-facing payloads into screen-oriented state shapes such as:

- summary cards
- top review items
- top daemon actions
- queue counts and section summaries
- detail action capabilities
- daemon panel cards and preview sections
- operator phase summary and implementation-detail sections for the post-app packaging/supervision line

## Boundary

The screen state builders:

- do not add new mutation capability
- do not replace the existing app-facing API contract
- do not commit to React, Tauri, webview, tray, or another final GUI framework

They are app-layer derivations over the existing resident app surfaces.

## Relationship to current payloads

The screen state builders sit on top of:

```text
/app/overview
/app/candidates
/app/candidates/{id}
/app/daemon-overview
```

They are intended to reduce repeated frontend-specific transformation logic.

The current Bridge now also exposes framework-neutral screen state endpoints:

```text
/app/screen-state/home
/app/screen-state/candidates
/app/screen-state/candidates/{id}
/app/screen-state/daemon
```

The extension layer now also has matching bridge-client fetch helpers for these endpoints.

For extension-hosted UI code, there is now also a background-message reader path for the same
screen states. This keeps bearer-token Bridge fetches inside the service worker while exposing
typed reader helpers to UI surfaces.

Current extension reader entrypoints:

```text
readHomeScreenState(send)
readCandidateQueueScreenState(send)
readCandidateDetailScreenState(send, candidateId)
readDaemonPanelScreenState(send)
```

The current extension side panel now uses these reader entrypoints for presentation-only
resident-app subpanels:

- queue summary over `readCandidateQueueScreenState(send)`
- candidate detail summary over `readCandidateDetailScreenState(send, candidateId)`
- daemon summary/detail over `readDaemonPanelScreenState(send)`

## Current daemon-panel detail scope

The current daemon screen state now also carries a conservative operator-phase detail section in
addition to the top-level summary cards and daemon preview payloads.

Current operator-phase daemon state includes:

- `operator_phase_summary` with phase, readiness, blocking reasons, and closure checklist
- `operator_phase_details.current_supported_operator_path` with the current startup command and
  bootstrap UI path
- `operator_phase_details.workstreams` with normalized workstream names, statuses, and one-line
  details
- `operator_phase_details.recommended_implementation_order`
- `operator_phase_details.read_surfaces`
- `operator_phase_details.exit_criteria`
- `operator_phase_details.not_in_scope`

This remains a read-only framing layer over the existing operator-phase contract. It does not add
service install controls, tray controls, or any proof-style daemon claims.

## Related documents

```text
docs/architecture/resident-app-ui-integration-contract.md
docs/architecture/resident-app-bootstrap-ui.md
docs/architecture/resident-app-ui-screen-map.md
```
