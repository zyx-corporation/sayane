# ADR 0028: `/app/ui-state/*` and `/app/ui-action/*` Remain Maintainer-Only Debug Seams on macOS

## Status

Accepted

## Date

2026-06-30

## Context

ADR 0014 reduced `/app/ui*` to a debug-only compatibility surface.

ADR 0027 then made the native macOS app the primary operator-facing path while keeping the Local
Bridge as the backend/helper behind that app.

That left one follow-up decision open:

- should `/app/ui-state/*` and `/app/ui-action/*` retire together with the browser HTML shell, or
- should they remain as explicit maintainer/debug transport seams even after routine operator flow
  is fully native-first?

Current implementation direction already shows a clean split:

1. the native macOS app reads and writes through bearer-backed `/app/*` resident surfaces
2. browser-local debug compatibility uses the dedicated local UI session plus `/app/ui-state/*` and
   `/app/ui-action/*`
3. routine startup, reconnect, install, handoff, and operator guidance no longer require those
   cookie-backed routes

This means the project can now decide the long-term role of the cookie-backed JSON routes without
blocking native macOS completion.

## Decision

On the macOS completion line, `/app/ui-state/*` and `/app/ui-action/*` remain as **maintainer-only
debug seams**.

That means:

1. they are no longer part of the normal operator-facing product path
2. they may continue to support explicit debug shell, smoke, fallback inspection, and maintainer
   diagnostics
3. they must stay contract-compatible with the existing local UI session model
4. they must not receive product-facing feature growth ahead of bearer-backed `/app/*` surfaces
5. retirement of server-rendered `/app/ui` HTML pages can be decided separately later if those
   pages become redundant

## Consequences

### Positive

- native macOS completion no longer depends on removing every browser-local debug transport
- maintainer/debug tooling can keep a same-origin session-based seam without reopening bearer
  handling inside browser-local checks
- smoke and fallback inspection can remain available while routine docs and UX stay native-first
- `/app/*` stays the only operator-facing integration contract the shipped macOS app depends on

### Negative

- the Bridge still carries an additional debug transport family that must remain tested and safe
- docs must keep explaining the difference between operator-facing `/app/*` and maintainer-only
  `/app/ui-state/*` / `/app/ui-action/*`
- full retirement of browser compatibility becomes a staged reduction, not a one-step deletion

## Boundaries

This decision does not:

- restore `/app/ui-state/*` or `/app/ui-action/*` as routine operator UX
- make the native macOS app depend on cookie-backed local UI sessions
- require server-rendered `/app/ui` HTML pages to remain forever
- change bearer-backed `/app/*` contracts used by the native app
- reopen Linux or Windows packaging priority

## Maintenance Rule

Until or unless a later ADR removes these seams entirely:

1. permit auth/session safety fixes, debug usability fixes, and smoke-contract fixes
2. do not add new product UX concepts there first
3. prefer adding operator capabilities to bearer-backed `/app/*` surfaces and native views
4. keep documentation labeling these routes as `maintainer`, `debug-only`, or `compatibility`

## Related

- `docs/adr/0014-app-ui-debug-only-compatibility-surface.md`
- `docs/adr/0027-macos-native-app-owns-the-operator-launch-experience-while-bridge-remains-the-local-backend.md`
- `docs/architecture/resident-app-bootstrap-ui.md`
- `docs/architecture/resident-app-ui-integration-contract.md`
- `docs/bridge-manual.md`
