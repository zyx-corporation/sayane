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

## Related

- `docs/adr/0013-macos-native-app-primary-ui-path.md`
- `docs/adr/0012-resident-app-production-auth-model.md`
- `docs/adr/0011-resident-app-local-ui-session-json-surfaces.md`
- `docs/architecture/resident-app-bootstrap-ui.md`
- `docs/architecture/resident-app-service-boundary.md`
