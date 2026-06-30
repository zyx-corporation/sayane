# ADR 0029: Server-Rendered `/app/ui` HTML Remains Removable After Maintainer Parity

## Status

Accepted

## Date

2026-06-30

## Context

ADR 0014 made `/app/ui*` a debug-only compatibility surface.

ADR 0028 then clarified that `/app/ui-state/*` and `/app/ui-action/*` remain on the macOS line as
maintainer-only debug seams even after routine operator flow is fully native-first.

That leaves one narrower question:

- should the server-rendered HTML pages under `/app/ui` remain indefinitely, or
- can they retire once maintainer/debug workflows have equivalent coverage through native views and
  the retained JSON debug seams?

The current codebase already separates those concerns:

1. native macOS operator flow uses bearer-backed `/app/*`
2. maintainer/debug transport can continue through `/app/ui-state/*` and `/app/ui-action/*`
3. the server-rendered HTML pages are presentation wrappers over the same underlying resident-app
   semantics

Because the JSON debug seams survive independently, the HTML layer no longer carries unique review
or mutation semantics.

## Decision

The server-rendered `/app/ui` HTML family is now treated as a **removable compatibility
presentation layer**.

It remains available for now, but it may retire once all of the following are true:

1. routine operator startup, review, diagnostics, recovery, install, and handoff stay closed in the
   native macOS app without browser fallback
2. maintainer/debug reads and writes needed for smoke or local diagnostics are covered by native
   views, CLI, or the retained `/app/ui-state/*` and `/app/ui-action/*` seams
3. smoke and runbook material no longer requires HTML-page navigation as the preferred debug path
4. no remaining handoff or troubleshooting doc depends on HTML rendering specifically rather than
   on the underlying JSON/CLI/native information

## Consequences

### Positive

- the project can continue reducing browser-local surface area without forcing premature removal
- HTML retirement becomes an operational readiness question instead of a transport-contract question
- the remaining browser-local boundary is smaller and easier to explain

### Negative

- the codebase temporarily keeps both server-rendered HTML and JSON debug presentation paths
- docs must distinguish between removable HTML presentation and retained debug transport seams

## Boundaries

This decision does not:

- remove `/app/ui` immediately
- remove `/app/ui-state/*` or `/app/ui-action/*`
- change the native macOS app integration contract
- re-open `/app/ui` as a product-facing routine operator surface

## Related

- `docs/adr/0014-app-ui-debug-only-compatibility-surface.md`
- `docs/adr/0028-ui-state-ui-action-remain-maintainer-debug-seams-on-macos.md`
- `docs/architecture/resident-app-bootstrap-ui.md`
- `docs/bridge-manual.md`
