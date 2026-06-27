# ADR 0016: MVP Native-First Operator Boundary Closure

## Status

Accepted

## Date

2026-06-27

## Context

ADR 0013 moved the primary operator-facing path to the native macOS application.

ADR 0014 then demoted `/app/ui*` to a debug-only compatibility surface.

ADR 0015 clarified that the supported packaging line remains `cli_first_local_bridge`, but it still
left the post-app packaging / supervision / recovery line in an intentionally open phase.

At this point, the Community MVP needs an explicit closure statement for the native-first app line
so that:

1. release and acceptance docs stop implying an unfinished primary path
2. native macOS app guidance can be treated as the routine operator workflow
3. post-MVP work is separated from MVP completion rather than smuggled back into it

## Decision

The Community MVP closes with the following operator boundary:

1. supported packaging model remains `cli_first_local_bridge`
2. native macOS app is the primary operator-facing workflow on macOS
3. `/app/ui*` remains debug-only compatibility, not the routine path
4. MVP service lifecycle support is limited to the current macOS LaunchAgent-adjacent preview/apply/bootstrap/bootout/kickstart line plus explicit local CLI control
5. service install / enable / disable / remove / update remain outside MVP support
6. MVP supervision remains `passive_local_observation_with_cli_recovery`
7. background supervision surfaces remain post-MVP ideas, not shipped MVP controls
8. mutating recovery remains explicit CLI confirmation only
9. native app clipboard capture is part of the MVP primary path

## Consequences

### Positive

- native-first release/readiness docs can describe one stable routine path
- operator summaries can mark the packaging/supervision/recovery boundary as closed for MVP
- post-MVP work becomes easier to scope as new packaging/service/supervision expansion rather than
  “still unfinished MVP”

### Negative

- macOS becomes intentionally ahead of Linux and Windows for operator UX
- the repo still carries debug-shell compatibility and cross-platform contract surfaces that are no
  longer part of MVP completion

## Boundaries

This decision does not:

- turn `/app/ui*` into a removed legacy surface yet
- add background supervision shipment
- add supported cross-platform OS service packaging
- add direct profile patch UI
- add Local Vault / encryption completion

## Related

- `docs/adr/0013-macos-native-app-primary-ui-path.md`
- `docs/adr/0014-app-ui-debug-only-compatibility-surface.md`
- `docs/adr/0015-current-supported-operator-packaging-model.md`
- `docs/release/v1.0.15-operator-packaging-supervision-phase-plan.md`
