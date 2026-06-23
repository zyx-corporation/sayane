# ADR 0013: macOS Native Application Becomes the Primary Resident App UI Path

## Status

Accepted

## Date

2026-06-22

## Context

ADR 0010 chose a Bridge-hosted local resident app shell as the first real resident UI container.

ADR 0011 and ADR 0012 then made that shell practical enough to exercise the resident app contract
through cookie-backed local JSON surfaces and a dedicated local UI session.

That work proved the current app-facing boundary, but it also exposed a product-direction mismatch:

- the Bridge-hosted web UI is useful as a bootstrap and debugging surface
- it is not yet better than the existing extension in day-to-day operator UX
- browser bootstrap, session continuity, and bridge liveness are too visible in the current flow
- the current operator path already assumes local-only runtime, LaunchAgent-oriented macOS service
  expectations, and app-facing resident endpoints that a native client can consume directly

At the same time, the current packaging and supervision plan already treats final operator-facing UI,
OS service integration, and supervision UX as post-shell work rather than as unfinished pieces of
the Bridge-hosted web surface.

## Decision

The project treats the current Bridge-hosted resident web UI as a bootstrap, debugging, and handoff
surface, not as the final primary operator UX.

The primary UI path now moves to a native macOS application that consumes the existing resident
app-facing read and write surfaces.

Near-term implementation direction:

1. keep the current resident app contract and screen-state surfaces as the integration boundary
2. build a macOS-native shell that hides bearer bootstrap and local UI session details from the
   operator
3. use the current Bridge and LaunchAgent line as the operational backend until a later packaging
   decision changes that architecture

The extension remains out of scope for this shift unless separately directed. It is neither revived
as the long-term primary path nor used as the target container for this native-app decision.

## Consequences

### Positive

- The team can improve operator UX where the current friction actually exists: startup, liveness,
  review navigation, and local recovery.
- The existing resident app contract, overview payloads, screen-state builders, and action surfaces
  remain reusable instead of being discarded.
- macOS-specific runtime expectations such as LaunchAgent-based supervision can become first-class
  UX flows instead of being indirectly represented through browser bootstrap steps.
- The Bridge-hosted web shell can remain available for debugging, tests, and handoff without
  constraining the final operator experience.

### Negative

- The project will temporarily carry both a Bridge-hosted shell and a macOS-native UI path.
- Browser-based resident shell refinements that do not help the macOS migration become lower
  priority.
- Cross-platform desktop packaging remains unresolved while the primary UX shifts first to macOS.

## Boundaries

This decision does not:

- remove the current Bridge-hosted web UI
- change the candidate review boundary or daemon proof/readiness boundaries
- commit the project to replacing the Bridge backend immediately
- decide Linux or Windows desktop packaging
- reopen the current instruction to leave the extension untouched for now

## Related

- `docs/adr/0010-resident-app-first-real-ui-container.md`
- `docs/adr/0011-resident-app-local-ui-session-json-surfaces.md`
- `docs/adr/0012-resident-app-production-auth-model.md`
- `docs/architecture/resident-app-ui-integration-contract.md`
- `docs/macos-launchagent.md`
- `docs/release/v1.0.15-operator-packaging-supervision-phase-plan.md`
