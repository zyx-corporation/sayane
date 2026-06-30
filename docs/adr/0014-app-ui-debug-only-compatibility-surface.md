# ADR 0014: `/app/ui` Becomes a Debug-Only Compatibility Surface

## Status

Accepted

## Date

2026-06-25

## Context

ADR 0013 moved the primary resident app UI path to the native macOS application.

The Bridge-hosted `/app/ui` family remains useful for:

- bootstrap and local session diagnostics
- browser-local smoke tests
- operator handoff and fallback inspection
- compatibility checks while native UX is still closing remaining gaps

At the same time, keeping `/app/ui` as if it were a normal operator-facing entrypoint now creates
directional drift:

- it keeps browser bootstrap visible in primary docs
- it makes debug-shell transport details look like product UX commitments
- it weakens the distinction between native steady-state UX and browser fallback

## Decision

The project now treats `/app/ui` and its related cookie-backed surfaces as a **debug-only
compatibility surface**.

That means:

1. the native macOS application is the primary operator-facing UI path
2. `/app/ui` remains available for debugging, smoke validation, fallback inspection, and handoff
3. primary docs, smoke scripts, and runbooks should prefer native-first language and flows
4. debug-shell checks should be explicit and opt-in where practical, rather than silently defining
   the default operator path

The retained Bridge-hosted compatibility surface currently includes:

```text
GET  /app/ui
GET  /app/ui/candidates
GET  /app/ui/candidates/{id}
GET  /app/ui/candidates/{id}/diff
GET  /app/ui/daemon

GET  /app/ui-state/*
POST /app/ui-action/*
```

## Consequences

### Positive

- primary onboarding can converge on native-first UX
- browser bootstrap details move out of the main operator path
- smoke and release checks can separate native coverage from debug-shell compatibility coverage
- later removal of `/app/ui` becomes a staged compatibility decision instead of a product-direction
  reversal

### Negative

- the project temporarily carries both native-first and debug-shell compatibility docs
- some existing scripts and tests still need explicit migration to reflect the new default
- `/app/ui` remains a live maintenance surface until native parity is sufficient

## Boundaries

This decision does not:

- remove `/app/ui` immediately
- remove `/app/ui-state/*` or `/app/ui-action/*` immediately
- change bearer-backed `/app/...` resident endpoint contracts
- change candidate review boundaries or daemon preview boundaries
- commit Linux or Windows desktop packaging

## Exit Criteria for Future Removal

`/app/ui*` may move from debug-only compatibility surface to removable legacy surface once:

1. native bootstrap and reconnect no longer depend on browser fallback
2. native review and daemon flows cover the sustained operator workflow
3. smoke and runbook paths no longer require browser-local validation for routine readiness checks
4. remaining handoff/debug needs are covered by explicit internal diagnostics or native exports

## Current Maintenance Boundary

Until those exit criteria are met, the retained `/app/ui*` surface should be maintained only under
the following boundary:

1. keep it available for explicit debug, smoke, fallback inspection, and historical handoff needs
2. do not expand it as a product-facing routine operator UX
3. prefer copy/export/diagnostic helpers over browser-opening shortcuts in current native flows
4. keep current docs native-first; if `/app/ui*` is mentioned, label it as debug-only or historical
5. allow compatibility-preserving fixes and auth/session safety fixes, but avoid new feature growth

## Current Retirement Readiness Snapshot

As of 2026-06-30:

- native bootstrap, reconnect, install, upgrade, and diagnostics are available from the macOS app
- routine startup, recovery, and handoff/export no longer require browser-opening defaults
- retained `/app/ui*` references now mostly live in debug-only, bridge-manual, smoke, and historical
  release/handoff material

Remaining work before full removal is primarily:

1. finish shrinking current smoke/runbook dependence on browser-local validation
2. decide separately when the server-rendered `/app/ui` HTML pages themselves can retire
3. keep the retained cookie-backed JSON routes under explicit maintainer/debug governance

That follow-on decision is now recorded in `docs/adr/0028-ui-state-ui-action-remain-maintainer-debug-seams-on-macos.md`.

## Related

- `docs/adr/0013-macos-native-app-primary-ui-path.md`
- `docs/adr/0012-resident-app-production-auth-model.md`
- `docs/adr/0011-resident-app-local-ui-session-json-surfaces.md`
- `docs/adr/0028-ui-state-ui-action-remain-maintainer-debug-seams-on-macos.md`
- `docs/architecture/resident-app-bootstrap-ui.md`
- `docs/architecture/resident-app-service-boundary.md`
