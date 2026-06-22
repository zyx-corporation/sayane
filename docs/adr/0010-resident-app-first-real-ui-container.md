# ADR 0010: Resident App First Real UI Uses a Bridge-Hosted Local Web App Shell

## Status

Accepted

## Date

2026-06-20

## Context

Sayane already has:

- app-facing resident app read/write endpoints
- framework-neutral screen-state endpoints
- a local Bridge HTML bootstrap UI
- an extension sidepanel that can read the same resident app screen-state surfaces

However, the project still needed to decide what the first real resident app UI container should
be after the bootstrap HTML phase.

The main candidates were:

1. continue growing the Bridge-hosted local UI into the first real app shell
2. move the first real shell into the Chrome extension sidepanel
3. introduce a new desktop/container framework before the resident app UI flow is stabilized

The existing documents already established important constraints:

- the bootstrap HTML is not the final GUI framework
- `GET /app/overview` remains the primary read model
- screen-state routes exist to reduce frontend-specific derivation logic
- candidate mutation must stay inside the existing review endpoints
- daemon wording must remain preview/observation only

The extension manual also records that the Chrome extension is freeze/deprecated and is no longer
the primary target for new UI work.

## Decision

The first real resident app UI container uses a Bridge-hosted Sayane Resident App local shell.

This means the next implementation phase should:

- keep Local Bridge as the host/runtime boundary for the first real Sayane Resident App UI shell
- build the first real UI on top of the existing app-facing endpoints and screen-state endpoints
- treat the current bootstrap HTML as a fallback and compatibility seam during transition
- keep the extension sidepanel as a compatibility/read-only-adjacent surface, not the primary new
  resident app shell

This decision does not yet choose the final long-term desktop packaging model.

It chooses the first real implementation container for the resident app UI slice.

## Rationale

### Why not the extension sidepanel

The extension is already documented as freeze/deprecated.

Using it as the primary new resident app shell would conflict with the current product direction
and would re-center UI growth on a compatibility surface.

### Why not a brand-new desktop container first

Introducing a new desktop/container framework before stabilizing the resident app UI flow would
mix two decisions:

- app workflow and screen-state correctness
- packaging/runtime/container choice

The project already has a stable local Bridge boundary and reusable screen-state routes. Reusing
them first keeps the next slice focused.

### Why a Bridge-hosted Sayane Resident App local shell

This path:

- keeps `GET /app/overview` as the primary read model
- reuses the existing localhost app-facing boundary
- reuses framework-neutral screen-state builders
- allows the bootstrap HTML to remain a fallback during migration
- avoids inventing a second mutation or auth boundary before the real UI flow is proven

## Consequences

### Positive

- The next real UI slice can start immediately from existing Bridge and screen-state surfaces.
- The extension remains compatible without becoming the primary growth surface.
- Desktop packaging can be deferred until the resident app workflow is stable.
- The migration from bootstrap HTML to real UI can happen incrementally under one local host.

### Negative

- The first real resident app shell still depends on Local Bridge runtime availability.
- A later desktop packaging/container decision remains open.
- There may be a temporary period where bootstrap HTML and the real Sayane Resident App UI shell coexist.

## Follow-up

Follow-up implementation should proceed in this order:

1. home screen on `GET /app/overview` or `GET /app/screen-state/home`
2. candidate queue
3. candidate detail and diff
4. candidate action flow
5. clipboard capture entry
6. daemon panel
7. MVP UI state handling and regression coverage

The later production issues may still revisit:

- final auth model
- final visual/interaction system
- extension/app alignment
- desktop/container packaging

But those are subsequent decisions, not blockers for the first real resident app shell.
