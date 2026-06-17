# Resident Daemon Process Identity Verification Policy

Status: Future verification policy

Related issues: #208, #209

## Summary

This document defines the policy boundary for future resident daemon process identity verification.

A future process existence check may show that some process exists for a PID. That is still not proof that the process is the expected Sayane resident daemon.

## Evidence position

Process identity is stronger than process existence:

```text
PID parse validity -> process existence -> process identity -> daemon readiness -> API readiness
```

Process identity means that the observed process is tied to the expected Sayane resident daemon instance for the expected runtime root.

## Why process existence is insufficient

A process with the parsed PID may be:

- an unrelated process
- a process from another Sayane runtime root
- a process from another user
- a reused PID after a stale PID file
- a partially launched helper process
- a malicious or confused process imitating weak metadata

Therefore process existence must not be treated as Sayane daemon identity.

## Future identity evidence candidates

Future process identity proof may require multiple independent signals.

Possible evidence sources include:

- runtime-root scoped lock ownership
- daemon-issued nonce challenge through authenticated local IPC
- signed runtime metadata
- expected executable metadata
- expected command metadata
- matching runtime root in daemon-reported metadata
- fresh boot/session epoch metadata
- capability-bound local handshake

No current Sayane command implements these checks.

## Socket presence is not identity proof

A socket file or open socket proves only that a socket-like artifact or endpoint exists.

It does not prove that:

- the endpoint is Sayane
- the endpoint belongs to the expected runtime root
- the endpoint is authenticated
- the endpoint is authorized
- the endpoint is protocol-compatible
- the endpoint is fresh

Socket presence must not be used as process identity proof by itself.

## Runtime-root scoping

Process identity must be scoped to the expected runtime root.

A valid identity proof for one runtime root must not prove identity for another runtime root.

A future identity diagnostic must include enough metadata to show which runtime root the evidence was bound to.

## Conservative future statuses

Future diagnostics should use conservative statuses such as:

```text
process_identity_unverified
process_identity_probe_unsupported
process_identity_permission_denied
process_identity_mismatch
process_identity_ambiguous
process_identity_verified
manual_review_required
```

A status such as `process_exists_identity_unverified` is preferred over `running` when only process existence is known.

## Non-goals for current preview work

Current Sayane commands do not:

- inspect arbitrary process command lines
- verify executable identity
- perform authenticated IPC handshakes
- create sockets
- send signals
- control processes
- prove daemon readiness
- prove API readiness

## Required future safety properties

A future identity proof must be:

- stronger than PID existence
- runtime-root scoped
- freshness-aware
- conservative under ambiguity
- explicit about permission limits
- separated from daemon control
- separated from cleanup or repair

## Relationship to readiness

A verified Sayane process identity does not prove daemon readiness.

The daemon may still be:

- starting
- degraded
- blocked
- shutting down
- running incompatible state
- unable to serve the requested operation class

Readiness remains a separate evidence layer.

## RDE Delta-M Review

### Preserved

Evidence claims remain staged and auditable.

Process control remains out of scope.

### Supplemented

The roadmap now distinguishes `some process exists` from `the expected Sayane resident daemon exists`.

### Deviation Risks

Do not use PID existence as identity proof.

Do not use socket presence as identity proof.

Do not let convenience metadata become a security boundary without freshness and runtime-root scoping.
