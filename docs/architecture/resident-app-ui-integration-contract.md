# Resident App UI Integration Contract

Status: app-facing integration contract

## Goal

This document gives UI implementers one stable integration path for the current resident app phase.

The intended starting point is:

```text
GET /app/contract
```

Then:

```text
GET /app/overview
```

The extension layer now also has typed bootstrap readers for this first read path:

```text
readAppContract(send)
readAppOverview(send)
```

For a human-visible local bootstrap, the current implementation also provides:

```text
GET /app/ui
```

`GET /app/ui` is a server-rendered local HTML screen built from the same contract and overview
payloads. It is a bootstrap surface, not a final GUI framework commitment.

The current implementation also provides local HTML review navigation:

```text
GET /app/ui/candidates
GET /app/ui/candidates/{id}
GET /app/ui/candidates/{id}/diff
```

These screens are presentation-only wrappers over the same app-facing candidate and diff payloads.

The current implementation also provides a local HTML daemon panel:

```text
GET /app/ui/daemon
```

This is a presentation wrapper over the existing `GET /app/daemon-overview` style preview surface.

The Bridge-hosted Sayane Resident App local shell also provides cookie-backed same-origin JSON reads and writes:

```text
GET /app/ui-state/contract
GET /app/ui-state/home
GET /app/ui-state/candidates
GET /app/ui-state/candidates/{id}
GET /app/ui-state/candidates/{id}/diff
GET /app/ui-state/candidates/{id}/lineage
GET /app/ui-state/daemon

POST /app/ui-action/capture-clipboard
POST /app/ui-action/candidates/{id}/evaluate
POST /app/ui-action/candidates/{id}/approve
POST /app/ui-action/candidates/{id}/reject
POST /app/ui-action/candidates/{id}/revise
```

For local bootstrap usage, the current implementation also provides cookie-backed HTML form actions:

```text
POST /app/ui/capture-clipboard
POST /app/ui/candidates/{id}/evaluate
POST /app/ui/candidates/{id}/approve
POST /app/ui/candidates/{id}/reject
POST /app/ui/candidates/{id}/revise
```

The initial `GET /app/ui` request uses the Bridge bearer token as a bootstrap credential. After
that, the local HTML surface and the local JSON shell surfaces continue with a dedicated local UI
session cookie issued by the Bridge-hosted resident shell. The raw Bridge bearer is no longer the
steady-state browser credential for follow-up local UI activity.

The current bootstrap HTML also adds lightweight redirect-based feedback for:

- success notices after local form actions
- invalid transition / validation errors returned to the relevant HTML screen

## Primary read model

The preferred initial screen payload is:

```text
GET /app/overview
  -> resident_app_overview
```

This payload already includes:

- runtime diagnostics
- UI-friendly summary counts
- review queue preview
- MCP preview
- daemon overview preview

UI code should treat this as the default first fetch.

## Focused follow-up reads

When the initial screen needs more detail, use:

```text
GET /app/candidates
GET /app/candidates/{id}
GET /app/candidates/{id}/diff
GET /app/daemon-overview
```

If the next GUI phase prefers framework-neutral screen state instead of raw payload composition, it
can also use:

```text
GET /app/screen-state/home
GET /app/screen-state/candidates
GET /app/screen-state/candidates/{id}
GET /app/screen-state/daemon
```

Current Bridge wiring should keep these screen-state routes derived from the same app-layer queue/detail/daemon builders used by the JSON and bootstrap HTML surfaces, so presentation refinements do not fork the underlying review semantics.

For the Bridge-hosted Sayane Resident App local shell specifically, the preferred same-origin JSON reads are now:

```text
GET /app/ui-state/home
GET /app/ui-state/candidates
GET /app/ui-state/candidates/{id}
GET /app/ui-state/candidates/{id}/diff
GET /app/ui-state/candidates/{id}/lineage
GET /app/ui-state/daemon
```

For extension-hosted UI surfaces, the preferred wiring is now:

```text
UI -> typed background message -> service worker Bridge fetch -> screen state payload
```

This keeps the bearer token in the background worker instead of duplicating Bridge auth handling in
each UI surface.

The current extension side panel now uses this pattern for a resident-app summary header:

```text
readAppContract(send)
readHomeScreenState(send)
```

This header is presentation-only. It gives local summary cards, top review items, daemon next
actions, and quick-link hints above the existing candidate review list.

Recommended usage:

- review list screen -> `GET /app/candidates`
- review detail screen -> `GET /app/candidates/{id}`
- review diff panel -> `GET /app/candidates/{id}/diff`
- daemon panel -> `GET /app/daemon-overview`

## Write surfaces

Current app-facing writes are:

```text
POST /app/capture-clipboard
POST /app/candidates/{id}/evaluate
POST /app/candidates/{id}/revise
POST /app/candidates/{id}/approve
POST /app/candidates/{id}/reject
```

These writes stay inside the candidate/review boundary.

They do not directly patch profile state outside the existing approval flow.

The Bridge-hosted Sayane Resident App local shell mirrors those same semantics through:

```text
POST /app/ui-action/capture-clipboard
POST /app/ui-action/candidates/{id}/evaluate
POST /app/ui-action/candidates/{id}/revise
POST /app/ui-action/candidates/{id}/approve
POST /app/ui-action/candidates/{id}/reject
```

These are transport variants for the local shell, not a separate review policy.

## Screen mapping

Suggested minimal screen mapping:

### Home / Dashboard

- source: `GET /app/overview`
- use:
  - `summary`
  - `review_summary`
  - `mcp_summary`
  - `daemon_summary`

### Candidate Queue

- source: `GET /app/candidates`
- use:
  - `items`
  - `reviewable_count`
  - `status_counts`
  - `top_sections`

### Candidate Detail

- source: `GET /app/candidates/{id}`
- use:
  - candidate payload
  - `ui_summary`
  - `allowed_actions`
  - proposal detail
  - evaluation state

### Candidate Diff

- source: `GET /app/candidates/{id}/diff`
- use:
  - raw diff payload
  - `ui_summary` for section / list-operation / count-oriented presentation before raw JSON inspection

### Daemon Panel

- source: `GET /app/daemon-overview`
- use:
  - `status`
  - `liveness`
  - `readiness`
  - `next_actions`

## Recommended interaction flow

```text
1. GET /app/contract
2. GET /app/overview
3. POST /app/capture-clipboard
4. GET /app/candidates
5. GET /app/candidates/{id}
6. GET /app/candidates/{id}/diff
7. POST /app/candidates/{id}/evaluate
8. POST /app/candidates/{id}/revise
9. POST /app/candidates/{id}/approve or /reject
```

For the Bridge-hosted Sayane Resident App local shell, the equivalent same-origin flow is:

```text
1. GET /app/ui
2. GET /app/ui-state/home
3. POST /app/ui-action/capture-clipboard
4. GET /app/ui-state/candidates
5. GET /app/ui-state/candidates/{id}
6. GET /app/ui-state/candidates/{id}/diff
7. GET /app/ui-state/candidates/{id}/lineage
8. POST /app/ui-action/candidates/{id}/evaluate
9. POST /app/ui-action/candidates/{id}/revise
10. POST /app/ui-action/candidates/{id}/approve or /reject
```

## Retained boundaries

Current phase still preserves:

- no direct profile patch endpoint for UI
- no daemon identity proof
- no daemon readiness proof
- no API readiness proof
- no OS service integration
- no final GUI framework commitment

## Handoff note

UI implementers should prefer the contract and overview payloads first, and add endpoint-specific
fetches only when one screen actually needs deeper detail.

## Framework-neutral screen states

The current app layer also provides framework-neutral screen state builders:

```text
build_home_screen_state(overview)
build_candidate_queue_screen_state(queue_payload)
build_candidate_detail_screen_state(detail_payload)
build_daemon_panel_screen_state(daemon_payload)
```

These builders are intended for the next GUI phase so that screen-level state can be reused without
committing to a specific frontend framework.

## See also

```text
docs/architecture/resident-app-ui-screen-map.md
docs/architecture/resident-app-bootstrap-ui.md
docs/architecture/resident-app-screen-state-contract.md
docs/adr/0011-resident-app-local-ui-session-json-surfaces.md
docs/release/v1.0.14-ui-implementation-task-breakdown.md
docs/release/v1.0.14-resident-app-surface-handoff.md
```
