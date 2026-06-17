# Resident Daemon Process Liveness Proof Policy

Status: Draft policy for future resident daemon work

Related issues: #202, #204

## Summary

This document defines the safety and evidence boundary for any future resident daemon process liveness proof in Sayane.

The current resident daemon preview sequence intentionally stops before process probing and process control:

```text
identity preview
-> lifecycle preview
-> operation plan preview
-> runtime layout preview
-> stale artifact diagnostic preview
-> cleanup decision preview
-> PID file parse diagnostic preview
```

The PID file diagnostic preview can parse planned PID file content, but parsing alone is never a liveness proof.

## Current boundary

Current resident daemon diagnostics are read-only preview surfaces.

They do not:

- start a daemon
- stop a daemon
- restart a daemon
- supervise a daemon
- probe a process
- send signals
- inspect OS process tables
- write PID files
- acquire locks
- create sockets
- create runtime directories
- delete or repair stale artifacts

This policy preserves that boundary until a separate future design explicitly introduces stronger runtime evidence.

## Definitions

### PID parse validity

PID parse validity means that PID file content was read as a positive integer string.

This proves only a property of file content.

It does not prove:

- the process exists
- the process is alive
- the process is Sayane
- the daemon is ready
- the resident API is reachable
- the daemon owns the current runtime root

### Process existence

Process existence means that an operating system reports a process for a given PID at the time of observation.

Process existence is still not enough to prove Sayane daemon identity. PIDs may be reused, stale PID files may point to unrelated processes, and OS observations may be permission-limited or platform-specific.

### Process identity

Process identity means there is evidence that the observed process is the expected Sayane resident daemon process.

Future process identity proof may require multiple independent signals, such as command metadata, runtime-root scoped lock ownership, daemon-issued nonce exchange, signed runtime metadata, or authenticated local IPC handshake.

No current Sayane command performs this proof.

### Daemon readiness

Daemon readiness means that the resident daemon has completed its initialization and is prepared to accept the intended local operation class.

A live process may still be starting, degraded, wedged, shutting down, or running with incompatible state. Therefore process existence and process identity are not sufficient to prove readiness.

### API readiness

API readiness means that a future local resident API endpoint is reachable, authenticated, authorized, and semantically compatible with the caller.

API readiness is stronger than process existence and process identity. It must not be inferred from a PID file.

## Evidence ladder

Future resident daemon evidence should be modeled as a ladder rather than a single boolean:

```text
pid_file_missing
pid_file_unreadable
pid_file_empty
pid_file_invalid
pid_file_parsed
process_existence_unverified
process_exists_unidentified
process_identity_unverified
process_identity_verified
readiness_unverified
readiness_verified
api_readiness_unverified
api_readiness_verified
```

The exact status names may change when implementation begins. The important rule is that every stronger claim must have a stronger evidence source.

## Minimum future liveness proof requirements

A future command may claim daemon liveness only if it can demonstrate all of the following at observation time:

1. PID file parse validity, if a PID file is part of the proof chain.
2. Process existence for the observed PID, using a documented platform-specific method or platform-neutral handshake.
3. Process identity evidence tying the observed process to Sayane resident daemon ownership.
4. Runtime-root scoping, so evidence is not accidentally borrowed from another Sayane runtime root.
5. Freshness evidence, so a stale PID or stale metadata file is not treated as current.
6. A conservative failure mode when any evidence source is ambiguous, unavailable, permission-denied, or contradictory.

A future command may claim daemon readiness only if liveness is already established and the daemon itself reports a ready state through a local authenticated channel.

A future command may claim API readiness only if the target local API surface is reachable, authenticated, authorized, and protocol-compatible.

## Conservative diagnostic statuses

Future liveness diagnostics should prefer conservative statuses such as:

```text
missing
unreadable
invalid
parsed_not_proof
process_unverified
process_probe_unsupported
process_probe_permission_denied
process_not_found
process_identity_unverified
process_identity_mismatch
liveness_unverified
liveness_verified
readiness_unverified
readiness_verified
api_readiness_unverified
api_readiness_verified
manual_review_required
```

The preview layer should avoid a plain `running` status unless the evidence model is strong enough to define what `running` proves.

## Trust boundaries

### Local-user boundary

Resident daemon liveness proof is local-user scoped by default.

Future diagnostics must not assume root privileges, global daemon ownership, or cross-user process inspection.

### Runtime-root boundary

A PID, lock, socket, or metadata artifact is meaningful only within its runtime root.

A future liveness proof must prevent evidence from one runtime root from proving liveness for another runtime root.

### Platform boundary

Process probing semantics differ across macOS, Linux, Windows, containers, and sandboxed environments.

Any future platform-specific probe must document:

- supported platform
- required permissions
- failure modes
- false-positive risks
- false-negative risks
- whether PID reuse can affect the result

### IPC boundary

A future local IPC handshake may provide stronger evidence than process-table inspection, but only if the endpoint itself is authenticated and runtime-root scoped.

An open socket alone is not process identity proof.

## Mutation boundary

Liveness diagnostics must remain separate from mutation.

Even a future `liveness_verified` result must not by itself authorize:

- PID file repair
- stale artifact deletion
- lock stealing
- daemon restart
- socket recreation
- OS service repair

Any such operation requires a separate mutating command, explicit operator intent, and its own safety policy.

## Current command implications

The current command:

```bash
sayane app daemon-pid-diagnostic --json
```

must continue to report that it does not prove liveness:

```text
proves_liveness: false
probes_process: false
controls_process: false
mutates_filesystem: false
```

The `parsed` status must continue to mean only that PID file content was parsed as a positive integer string.

## RDE Delta-M Review

### Preserved

The resident daemon remains staged and auditable.

Preview commands remain non-mutating.

PID file parsing remains explicitly separated from liveness proof.

### Supplemented

The resident daemon design now has an evidence ladder for future runtime claims:

```text
file evidence -> process evidence -> identity evidence -> readiness evidence -> API evidence
```

### Deviation Risks

Do not convert PID parse success into a `running` claim.

Do not introduce platform-specific process probing without documenting permission and false-positive boundaries.

Do not bind cleanup, repair, restart, or lock-stealing behavior to liveness diagnostics.

Do not treat socket presence as API readiness.
