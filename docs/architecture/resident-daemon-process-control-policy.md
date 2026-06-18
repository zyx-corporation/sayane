# Resident Daemon Process Control Policy

Status: Future process-control policy

Related issues: #207, #218, #219

## Summary

This document defines the policy for future resident daemon process control.

Process control includes starting, stopping, restarting, signaling, supervising, and recovering daemon processes.

Current Sayane resident daemon commands are preview-only and do not control processes.

## Core rule

Process control is a distinct high-risk operation class.

It must not be hidden behind diagnostics, lifecycle plans, runtime initialization, cleanup, repair, lock handling, or IPC readiness checks.

## Current boundary

Current commands do not:

- start a daemon
- stop a daemon
- restart a daemon
- send signals
- supervise processes
- recover daemon processes
- write PID files
- acquire locks
- create sockets
- create runtime directories
- integrate with OS service managers

This boundary remains until a separate future process-control implementation is explicitly accepted.

## Command classes

Future process-control commands may include:

```text
daemon-start
daemon-stop
daemon-restart
daemon-signal
daemon-supervise
daemon-recover
```

Each command requires separate implementation acceptance.

## Start prerequisites

A future `daemon-start` command requires:

- explicit operator intent
- runtime initialization policy acceptance
- runtime root validation
- lock acquisition policy acceptance
- PID write policy acceptance
- socket lifecycle policy acceptance if IPC is enabled
- local IPC authentication policy if an API is exposed
- audit record

Starting a daemon must not be a side effect of `daemon-plan`.

## Stop prerequisites

A future `daemon-stop` command requires:

- explicit operator intent
- process existence evidence
- process identity evidence
- target runtime-root scoping
- graceful shutdown policy
- timeout and fallback policy
- audit record

A parsed PID alone must not authorize stop.

## Restart prerequisites

A future `daemon-restart` command combines stop and start risks.

It requires:

- explicit operator intent
- verified target identity
- readiness/failure reason if available
- stop policy
- start policy
- recovery plan
- audit record

Restart must not be hidden inside repair or cleanup.

## Signal handling

Future signal operations require platform-specific policy.

A signal must not be sent unless the target process identity is verified and the operator intent is explicit.

Unsupported platforms and permission errors must fail closed.

## Supervision

Future supervision requires a separate state machine and failure policy.

Supervision must define:

- expected daemon states
- retry limits
- backoff policy
- failure escalation
- audit behavior
- operator override behavior

Supervision must not be introduced as an implicit background task.

## Recovery

Future recovery commands must distinguish:

```text
artifact recovery
runtime recovery
process recovery
IPC recovery
service recovery
```

These must not be collapsed into one broad repair command.

## Audit requirements

Future process-control commands must record:

- command name
- operator intent signal
- runtime root
- target PID if applicable
- process identity evidence
- readiness evidence where applicable
- mutation side effects
- result
- timeout or failure mode
- recovery note

## Relationship to OS service integration

Process control is not OS service integration.

Service managers add platform-specific behavior, privilege boundaries, and persistence. They require separate policy.

## RDE Delta-M Review

### Preserved

Resident daemon remains non-running in the current preview track.

Lifecycle plan commands remain plan-only.

### Supplemented

The roadmap now defines the process-control gate before actual daemon operation.

### Deviation Risks

Do not let lifecycle plan commands start or stop processes.

Do not treat process identity as authorization without operator consent.

Do not hide restart or recovery inside cleanup or repair commands.
