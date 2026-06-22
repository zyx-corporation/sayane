# ADR 0009: Resident Daemon MVP Uses Bridge Delegation

## Status

Accepted

## Date

2026-06-19

## Context

Sayane had already implemented preview-first resident daemon planning, runtime initialization, and
audit-shaped payloads, but it still lacked a running local daemon.

The project needed an MVP that could cross the line into actual process control without
simultaneously introducing:

- a second HTTP server implementation
- OS service integration
- a new IPC transport
- a new authentication stack
- broad cleanup or repair behavior

The main architectural question was whether the first MVP should build a brand-new resident server
or whether it should delegate to the existing local bridge implementation.

## Decision

The first resident daemon MVP uses bridge delegation.

`sayane app daemon-start` launches the existing `sayane serve` command as a local subprocess and
manages it through explicit control files under the resident runtime root.

The accepted MVP includes:

- `daemon-start`
- `daemon-stop`
- `daemon-restart`
- `daemon-status`
- runtime-root PID file
- runtime-root lock file
- readiness wait via `GET /health`

The MVP does not add:

- a second resident HTTP server
- OS service integration
- non-local bind support
- network exposure
- persistent credentials beyond existing bridge behavior
- cleanup apply or repair apply
- lock stealing

## Rationale

Bridge delegation minimizes new moving parts while still delivering a real daemon process.

It reuses:

- the existing FastAPI bridge app
- existing localhost boundary
- existing bridge token/auth behavior
- existing health endpoint

This keeps the first daemon MVP focused on process-control correctness rather than server feature
duplication.

## Consequences

### Positive

- The project now has a real local daemon start/stop/restart path.
- Runtime control stays local-only and explicit.
- The serving stack stays single-path and easier to debug.

### Negative

- Resident daemon identity remains coupled to the bridge process shape.
- A future dedicated resident server would require another transition decision.
- Lock handling remains conservative and single-user oriented.

## Follow-up

Future work may still replace bridge delegation with a dedicated resident server, but only after a
separate ADR accepts the transport, auth, migration, and audit consequences.
