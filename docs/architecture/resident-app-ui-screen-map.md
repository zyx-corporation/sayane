# Resident App UI Screen Map

Status: screen contract map

## Purpose

This document maps the current app-facing surfaces to the first Bridge-hosted Resident App local
shell.

It is intentionally implementation-neutral.

It does not choose React, Tauri, webview, or tray architecture.

The current Bridge-hosted Sayane Resident App local shell also keeps a shared shell header showing:

- current screen
- current candidate target when present
- current cookie-backed JSON surface

The current local shell also keeps a URL hash route for:

- `home`
- `queue`
- `detail` plus `candidate_id`
- `daemon`

## Screen 1: App Home

### Primary source

For bearer-based clients:

```text
GET /app/overview
```

For the Bridge-hosted Sayane Resident App local shell:

```text
GET /app/ui-state/home
```

### Use these fields

- `summary.repository_available`
- `summary.reviewable_count`
- `summary.approved_context_count`
- `summary.blocked_context_count`
- `summary.daemon_state`
- `summary.readiness_status`
- `summary.next_action_count`
- `review_summary.top_items`
- `daemon_summary.top_next_actions`

### UI intent

- show current review workload
- show whether MCP-derived context is populated
- show whether daemon/runtime attention is needed
- show the first likely actions without extra fetches
- expose quick links that can open queue and daemon panels without round-tripping through legacy HTML
- keep the current supported startup path and debug-shell fallback visible from the same first-pass
  operator surface, with the same launcher/debug actions used by the daemon and fallback screens

## Screen 2: Candidate Queue

### Primary source

For bearer-based clients:

```text
GET /app/candidates
```

For the Bridge-hosted Sayane Resident App local shell:

```text
GET /app/ui-state/candidates
```

### Use these fields

- `items`
- `reviewable_count`
- `is_review_surface`

### UI intent

- list pending or evaluated candidates
- allow drill-in to one candidate
- keep approved/rejected candidates out of the default queue surface
- surface `status_counts` and `top_sections` as first-class queue summaries rather than hiding them
  in one serialized blob

## Screen 3: Candidate Detail

### Primary source

For bearer-based clients:

```text
GET /app/candidates/{id}
```

For the Bridge-hosted Sayane Resident App local shell:

```text
GET /app/ui-state/candidates/{id}
```

### Use these fields

- candidate payload
- `proposal`
- `evaluation`
- `review_surface`

### UI intent

- show captured content and proposed target section
- show current evaluation state
- provide actions for diff, evaluate, revise, approve, reject
- keep lineage and diff inspection close to the same detail surface
- prefer compact detail / proposal / evaluation / diff / lineage summaries before raw payload
  inspection

Current extension sidepanel note:

- resident-app home summary cards now also expose active review source, candidate count, and whether the active candidate is visible in top review items
- resident-app top review items and queue items now keep the active review candidate pinned first when it is present
- resident-app quick links now prepend an active review detail route and keep queue navigation close to the top when an active review exists
- resident-app queue/detail panels now add explicit buttons to jump back to the active review candidate without returning through home
- when those active-review return buttons are unavailable, resident-app now explains whether no active review exists or the current detail already is the active review target
- the current Japanese resident-app copy now localizes most UI labels while preserving `active review` as the stable review-session concept name
- the same copy policy also preserves stable workflow terms such as `review card`, `contract`, `entrypoint`, `Cleanup preview`, and `Repair preview` where those names act as product concepts rather than generic labels
- resident-app detail stays presentation-only
- it now adds “next steps” handoff hints and buttons that route back into the existing review card
- it now also adds a compact lineage summary so the current candidate path is visible without leaving the resident-app panel
- resident-app header also shows the current active review candidate id derived from the same extension review-session state
- resident-app review/queue rows now highlight that same active candidate, and detail summary shows whether the current item is the active review target
- when review-session focus changes while the sidepanel stays open, resident-app preserves the visible panel and re-fetches the current home / queue / detail screen state for that surface instead of forcing a full reset
- if the visible detail candidate can no longer be loaded during that re-fetch, resident-app fail-closes back to queue instead of keeping stale detail content on screen
- queue summary now explicitly states whether the current active review candidate is still present in the fetched queue surface
- queue summary and detail summary also expose the current review-session source and candidate count so active review context stays visible inside the resident-app panel
- detail summary plus lineage/diff previews now add a compact note when the visible detail candidate is not the current active review candidate

## Screen 4: Candidate Diff

### Primary source

For bearer-based clients:

```text
GET /app/candidates/{id}/diff
```

For the Bridge-hosted Sayane Resident App local shell:

```text
GET /app/ui-state/candidates/{id}/diff
GET /app/ui-state/candidates/{id}/lineage
```

### UI intent

- explain what approval would change
- highlight section placement and add/remove semantics
- support explicit approval review

Current extension sidepanel note:

- resident-app detail panel now adds a presentation-only diff preview beside the detail screen state
- it uses the existing candidate diff read path after `GET /app/candidates/{id}`-equivalent detail state

## Screen 5: Candidate Revision

### Primary action

For bearer-based clients:

```text
POST /app/candidates/{id}/revise
```

For the Bridge-hosted Sayane Resident App local shell:

```text
POST /app/ui-action/candidates/{id}/revise
```

### UI intent

- let the user rewrite candidate content without mutating profile state
- create a new pending candidate rather than editing approved history in place

## Screen 6: Daemon Panel

### Primary source

For bearer-based clients:

```text
GET /app/daemon-overview
```

For the Bridge-hosted Sayane Resident App local shell:

```text
GET /app/ui-state/daemon
```

### Use these fields

- `status`
- `liveness`
- `readiness`
- `runtime_init`
- `cleanup_preview`
- `repair_preview`
- `next_actions`
- `operator_panels`
- `operator_phase_summary`
- `operator_phase_details`
- `service_target_summary`
- `launchagent_summary`

### UI intent

- inspect local daemon/runtime situation
- surface bounded operational next steps
- avoid overclaiming proof or readiness
- keep packaging / service / supervision / recovery gates visible as one aligned post-app read stack

## Global entry bootstrap

The recommended bearer-based startup sequence is:

```text
GET /app/contract
GET /app/overview
```

Use `GET /app/contract` only as bootstrap or compatibility guidance.

Use `GET /app/overview` as the real initial screen payload.

The Bridge-hosted Sayane Resident App local shell startup sequence is:

```text
GET /app/ui
GET /app/ui-state/home
```

## Current local shell mapping

The current local Bridge implementation maps those surfaces like this:

- `/app/ui` -> app home over `GET /app/overview`
- `/app/ui` embedded shell -> `GET /app/ui-state/home`
- shell queue -> `GET /app/ui-state/candidates`
- shell detail -> `GET /app/ui-state/candidates/{id}`
- shell diff -> `GET /app/ui-state/candidates/{id}/diff`
- shell lineage -> `GET /app/ui-state/candidates/{id}/lineage`
- shell daemon -> `GET /app/ui-state/daemon`
- shell actions -> `POST /app/ui-action/...`
- `/app/ui/candidates` -> candidate queue over `GET /app/candidates`
- `/app/ui/candidates/{id}` -> candidate detail over `GET /app/candidates/{id}`
- `/app/ui/candidates/{id}/diff` -> candidate diff over `GET /app/candidates/{id}/diff`
- `/app/ui/daemon` -> daemon panel over daemon overview preview

The current shell daemon view now treats these as the preferred derived read sections:

- `operator_panels`
- `operator_phase_summary`
- `operator_phase_details`
- `service_target_summary`
- `launchagent_summary`

This keeps the daemon shell summary-first while preserving the underlying preview/contract boundary.

The embedded shell and retained HTML routes are transport variants over the same app-facing
boundaries.

## Boundaries for all screens

- do not directly patch profile state
- do not bypass candidate review
- do not treat daemon preview as production proof
- do not infer API readiness from endpoint reachability alone
