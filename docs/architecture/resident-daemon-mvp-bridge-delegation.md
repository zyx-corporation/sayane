# Resident Daemon MVP Bridge Delegation

Status: Minimal implementation slice

## Summary

The first resident daemon MVP does not introduce a second server implementation.

Instead, `sayane app daemon-start` manages the existing `sayane serve` bridge as a local-only
subprocess and treats that bridge process as the resident daemon runtime.

## Scope

The MVP adds:

- explicit `daemon-start`
- explicit `daemon-stop`
- explicit `daemon-restart`
- actual `daemon-status`
- PID file write under the runtime root
- lock file write under the runtime root
- readiness wait against `GET /health`

## Retained constraints

The MVP remains:

- localhost-only
- single-user oriented
- explicit operator control only
- without OS service integration
- without network exposure
- without cleanup apply
- without repair apply
- without lock stealing

## Startup model

`daemon-start` requires runtime initialization to be completed first.

It then:

1. checks for stale PID/lock artifacts
2. creates a lock file
3. launches `python -m sayane.cli.main serve --host ... --port ...`
4. writes the spawned PID
5. waits for `/health`

If readiness does not succeed in time, the process is terminated and the control artifacts are
removed.

## Why this shape

This keeps the first process-control MVP narrow:

- one HTTP path
- one auth model
- one localhost transport
- one bridge implementation

It avoids inventing a parallel resident API server before the project proves that process control,
runtime layout, and audit shape are stable.
