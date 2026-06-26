# ADR 0015: Current Supported Operator Packaging Model Remains CLI-First With Native macOS Primary UI

## Status

Accepted

## Date

2026-06-25

## Context

ADR 0014 clarified that the browser-hosted `/app/ui` path is no longer the
primary operator-facing product direction.

At the same time, the project still has not closed the broader packaging /
service / supervision phase:

- background supervision remains deferred
- service lifecycle is only partially concrete on macOS
- Linux and Windows still share the common contract baseline rather than a
  shipped desktop/service packaging commitment

This means the project needs one explicit statement that separates:

1. the currently supported operator packaging model
2. the current primary operator UI on macOS
3. the still-deferred packaging candidates

## Decision

The currently supported operator packaging model remains:

`cli_first_local_bridge`

That supported line means:

1. the operator explicitly starts the local Bridge / CLI path
2. the current runtime remains local-only
3. no background supervision commitment is implied
4. no service-first daemon commitment is implied

Within that same supported packaging line:

- the native macOS app is the primary operator-facing UI on macOS
- the Bridge-hosted `/app/ui` path remains a debug / smoke / fallback /
  handoff compatibility surface

The project continues to model, but not support, the larger next candidates:

- `hybrid_local_bridge_plus_service_targets`
- `service_first_resident_runtime`

## Consequences

### Positive

- current docs, CLI summaries, and native UI can describe one stable supported
  line without implying service-phase closure
- native macOS UI can continue to improve without smuggling in a service-first
  packaging decision
- operator handoff and troubleshooting can state one recommended launcher path
  clearly

### Negative

- the project temporarily carries a split between current supported startup
  semantics and future service/supervision candidates
- cross-platform operator UX remains intentionally uneven until later phase
  closure

## Boundaries

This decision does not:

- close the operator packaging and supervision phase
- imply supported background supervision
- imply supported OS service lifecycle beyond the current explicit local
  boundaries
- change the review boundary or permit direct profile patch UI

## Related

- `docs/adr/0014-app-ui-debug-only-compatibility-surface.md`
- `docs/release/v1.0.15-operator-packaging-supervision-phase-plan.md`
- `docs/release/v1.0.14-resident-app-operator-handoff.md`
