# ADR 0027: macOS Native App Owns the Operator Launch Experience While Bridge Remains the Local Backend

## Status

Accepted

## Date

2026-06-29

## Context

ADR 0013 moved the primary operator-facing path to the native macOS application.

ADR 0014 then reduced `/app/ui*` to a debug-only compatibility surface, and ADR 0015 clarified that
the currently supported operator packaging line still remains `cli_first_local_bridge`.

That combination resolved product direction, but it still leaves one visible UX gap:

- the native macOS app is primary in product language
- the Bridge is still started and reasoned about as a separate operator concern
- repo-local launch scripts are still part of the day-to-day startup path
- browser and debug-shell fallback details are still too close to normal recovery steps

At the same time, the current runtime and service boundaries remain valuable:

- resident app read/write contracts already serve the native app correctly
- bridge delegation keeps the serving path single and debuggable
- CLI, Bridge, MCP, and native app still need a shared app-service boundary

The project therefore needs an explicit decision about the next macOS completion step: whether to
replace the Bridge backend immediately, or to first make the native app own the operator launch
experience while keeping the Bridge as an internal local backend.

## Decision

On macOS, the native application now owns the operator launch experience.

The accepted near-term direction is:

1. operator startup should begin from the native macOS app, not from repo-local Bridge scripts
2. the native macOS app may launch, warm up, and reconnect to the local Bridge as an internal
   helper/backend concern
3. the resident app contract, app-service boundary, and Bridge-backed localhost API remain the
   runtime integration seam until a later ADR replaces that backend
4. debug-only browser surfaces remain available for smoke, diagnostics, and handoff, but are no
   longer part of the normal macOS operator workflow

This means the project explicitly chooses **UX integration first, backend replacement later**.

## Consequences

### Positive

- operator-facing startup can converge toward a one-app mental model on macOS
- the project can remove repo-local launch friction without reopening service-boundary design
- existing resident app contracts, auth, and review boundaries remain reusable
- `/app/ui*` retirement can proceed from a stronger native diagnostic and recovery path

### Negative

- the architecture still temporarily contains two layers: native app and Bridge helper/backend
- packaging work must carry runtime bundling, helper launch, logging, and diagnostics details inside
  the macOS app path
- a later backend replacement decision is still required if the project wants to eliminate the
  Bridge process entirely

## Boundaries

This decision does not:

- replace the current Bridge backend with a new transport or server
- remove the resident app contract or app-service boundary
- commit Linux or Windows to the same packaging/runtime shape
- make `/app/ui*` removable immediately
- imply background service-first supervision beyond the current explicit local boundaries

## Implementation Direction

The expected macOS completion line now becomes:

1. eliminate routine dependence on repo-local launch scripts for normal operator startup
2. bundle or otherwise ship the required Bridge/helper runtime behind the native app entrypoint
3. provide native diagnostics and reconnect/start guidance sufficient to demote browser fallback
4. keep `/app/ui*` only for explicit debug/smoke/handoff use until the native path closes those
   remaining cases

## Related

- `docs/adr/0013-macos-native-app-primary-ui-path.md`
- `docs/adr/0014-app-ui-debug-only-compatibility-surface.md`
- `docs/adr/0015-current-supported-operator-packaging-model.md`
- `docs/adr/0009-resident-daemon-mvp-bridge-delegation.md`
- `docs/architecture/resident-app-service-boundary.md`
