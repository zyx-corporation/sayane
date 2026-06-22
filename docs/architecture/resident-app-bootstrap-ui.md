# Resident App Bootstrap UI

Status: bridge_hosted_local_shell_mvp

## Goal

This document records the current local Bridge HTML bootstrap UI for the Resident App.

The bootstrap UI started as a server-rendered navigation layer and now also hosts the first real
Bridge-local Sayane Resident App local shell.

It exists to make the current resident app surfaces human-navigable and interactable without
choosing the final production packaging or desktop container.

## Current local HTML surfaces

The current bootstrap UI provides:

```text
GET /app/ui
GET /app/ui/candidates
GET /app/ui/candidates/{id}
GET /app/ui/candidates/{id}/diff
GET /app/ui/daemon
```

It also provides local HTML form actions:

```text
POST /app/ui/capture-clipboard
POST /app/ui/candidates/{id}/evaluate
POST /app/ui/candidates/{id}/approve
POST /app/ui/candidates/{id}/reject
POST /app/ui/candidates/{id}/revise
```

It now also provides cookie-backed local shell JSON surfaces:

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

## Layering

The bootstrap UI keeps the following shape:

```text
local HTML screen / form
  -> Bridge resident_app routes
    -> resident app contract / overview / candidate / daemon surfaces
      -> ResidentRuntime / ResidentAppService / app UI usecases
        -> repository and review seams
```

The retained server-rendered HTML layer remains presentation-only.

The cookie-backed shell JSON layer must not become a parallel mutation model outside the existing
resident app and review surfaces.

## Auth seam

The bootstrap UI currently uses:

1. bearer token on the first `GET /app/ui` as the bootstrap or pairing credential
2. dedicated local UI session cookie for follow-up navigation, `/app/ui-state/*`, and `/app/ui-action/*`
3. local UI locale cookie for follow-up bootstrap HTML rendering after an explicit `?locale=` choice

The JSON shell endpoints under `/app/ui-state/*` and `/app/ui-action/*` reuse that same local UI
session cookie so a browser-local shell can fetch screen state and submit review actions without
embedding the bearer token into page JavaScript.

## Feedback seam

The bootstrap UI currently uses redirect-based feedback:

- success notices after local form actions
- validation / transition error feedback on return to the relevant screen

The current bootstrap UI also adds lightweight presentation refinements:

- queue-level visibility for evaluation level and RDE class
- queue-level pending/evaluated summary counts
- queue-level status-count and top-section summaries from the app-facing queue payload
- detail-level action guidance before approval
- direct home-to-candidate links from top review items
- detail-level proposal/evaluation metadata summaries with raw JSON fallback
- daemon preview sections that surface operation ids, preview hashes, and decision tables instead of raw dict-only dumps
- bootstrap HTML copy is now centralized in one renderer-local dictionary so later i18n externalization does not require reopening route or view-model logic
- bootstrap HTML locale selection currently normalizes to `ja` or `en`, sets `<html lang>`, and lets routes reuse the same query/cookie-backed locale seam without changing app-layer payloads
- the clipboard capture form now reflects the current bootstrap locale instead of hard-coding `ja`, so the bootstrap seam stays presentation-only while keeping locale round-trips explicit
- redirect-based notices and known review-transition errors now reuse the same bootstrap locale seam at render time; unknown error strings still pass through unchanged so review diagnostics are not hidden
- known status / boolean / preview tokens are now translated at render time in the bootstrap renderer, while app-layer payloads remain locale-neutral and keep their existing machine-readable values
- daemon preview tables now apply the same render-time token translation for known path roles, artifact kinds, and preview recommendations so bootstrap readability improves without rewriting app-layer preview payloads
- `dt` labels in metadata panels now use renderer-local display labels instead of raw payload keys, so operator-facing bootstrap screens stay readable without changing the underlying JSON contracts
- known section, source, and operation tokens shown in bootstrap HTML now also flow through the same display-only translation layer; form values and JSON contracts still keep the original machine tokens
- known daemon preview reasons and overview follow-up summaries now also pass through renderer-local display translation when they match the current local-only bootstrap vocabulary; unknown payload prose still renders unchanged
- the renderer-local bootstrap copy is now grouped by concern (`core`, `actions`, `labels`, `details`, `tables`, `fields`, `values`, `feedback`, `phrases`) so future i18n extraction can move one layer at a time without reopening route behavior
- `/app/ui` now embeds a small same-origin local shell that can navigate home / queue / detail /
  diff / lineage / daemon and submit candidate review actions through the new cookie-backed JSON
  surfaces while keeping the legacy server-rendered pages available as fallback links
- the embedded local shell now opens explicit in-shell action forms for evaluate / approve / reject /
  revise and disables unavailable actions from `allowed_actions` instead of relying on prompt-only
  mutation affordances
- the embedded local shell daemon view now renders summary cards, next actions, runtime-init /
  cleanup / repair preview metadata tables, and a retained raw observation panel instead of showing
  only a single JSON dump
- the embedded local shell home view now renders localized summary-card labels plus quick links from
  `HomeScreenState.quick_links`, and the queue view now renders summary-first status/top-section
  panels instead of collapsing those aggregates into one raw object string
- the embedded local shell now also renders a shared current-screen header that exposes the active
  shell screen, current candidate target when present, and the JSON surface currently backing the
  visible panel
- the embedded detail shell now renders compact summary cards for detail / proposal / evaluation /
  diff / lineage before the raw diff payload, so the shell can stay summary-first without removing
  the underlying JSON fallback
- the shared shell toolbar now reflects the active local shell screen, and home quick links render
  localized screen labels instead of raw screen contract tokens
- the embedded local shell now syncs its visible screen and candidate target into the URL hash so a
  reload can restore home / queue / detail / daemon state without falling back to legacy HTML routes
- the embedded local shell now reuses renderer-local field / table / token / phrase dictionaries for
  cards, metadata panels, queue tables, daemon preview tables, and lineage summaries, so visible UI
  copy can localize at render time without changing the locale-neutral JSON contracts

The underlying app-facing candidate payloads now also expose reusable GUI-oriented view-model data:

- queue `status_counts`
- queue `top_sections`
- detail `ui_summary`
- detail `allowed_actions`

The app layer now also provides framework-neutral screen state builders for:

- home
- candidate queue
- candidate detail
- daemon panel

The current Bridge HTML routes should reuse the same app-layer candidate queue/detail builders where possible, so HTML and JSON surfaces do not drift in status counts, top sections, or allowed-action summaries.

This keeps the current HTML flow simple while preserving the underlying app-facing boundary.

## Boundaries

The bootstrap UI must not:

- add direct profile patch UI
- bypass candidate evaluation and approval flow
- overclaim daemon or API readiness
- claim process identity proof
- commit to Tauri, React, webview, tray, or another final GUI framework

## Related documents

```text
docs/architecture/resident-app-service-boundary.md
docs/architecture/resident-app-ui-integration-contract.md
docs/architecture/resident-app-ui-screen-map.md
docs/adr/0011-resident-app-local-ui-session-json-surfaces.md
docs/release/v1.0.14-resident-app-bootstrap-ui-handoff.md
docs/release/v1.0.14-resident-app-bootstrap-ui-closure.md
```
