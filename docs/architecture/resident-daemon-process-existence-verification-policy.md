# Resident Daemon Process Existence Verification Policy

Status: Future verification policy

Related issues: #207, #208

## Summary

This document defines the policy boundary for future resident daemon process existence verification.

Current Sayane resident daemon diagnostics may parse a planned PID file and report:

```text
pid_parsed_process_unverified
```

That status intentionally means that process existence has not been verified.

## Evidence position

Process existence is the next evidence layer after PID parsing:

```text
PID parse validity -> process existence -> process identity -> daemon readiness -> API readiness
```

Process existence is weaker than process identity. It means only that an operating system or authenticated local mechanism reports that some process exists for an observed PID at observation time.

It does not prove that the process is Sayane.

## Why PID parsing is insufficient

A PID file is a filesystem artifact.

A parsed PID proves only that file content was shaped like a positive integer string. It does not prove that:

- an OS process exists for that PID
- the process is owned by the expected user
- the process belongs to the expected runtime root
- the process is the Sayane resident daemon
- the process is alive in a useful state
- the daemon is ready
- an API is reachable or authorized

## PID reuse risk

PIDs are reusable identifiers.

A stale PID file may point to:

- no process
- a new unrelated process
- a process owned by another user
- a process inside another container namespace
- a process from another Sayane runtime root

A future process existence check must treat PID reuse as a primary false-positive risk.

## Platform and permission boundaries

Process existence probing differs by platform.

A future implementation must document supported behavior for each target platform before enabling process probing:

- macOS
- Linux
- Windows
- containers
- sandboxed environments
- restricted permission environments

A permission-denied result must not be treated as process absence.

An unsupported platform must not be treated as process absence.

## Conservative future statuses

Future diagnostics should use conservative statuses such as:

```text
process_existence_unverified
process_probe_unsupported
process_probe_permission_denied
process_not_found
process_exists_identity_unverified
process_existence_ambiguous
manual_review_required
```

A plain `running` status should be avoided unless stronger evidence layers are also satisfied.

## Non-goals for current preview work

Current Sayane commands do not:

- probe operating-system processes
- send signals
- inspect OS process tables
- read arbitrary `/proc` state
- start a daemon
- stop a daemon
- restart a daemon
- supervise a daemon
- prove process identity
- prove daemon readiness
- prove API readiness

## Required future safety properties

A future process existence check must be:

- local-user scoped by default
- runtime-root scoped where possible
- conservative under permission errors
- explicit about unsupported platforms
- explicit about PID reuse risks
- separated from process control
- separated from cleanup or repair decisions

## Relationship to cleanup

Process existence verification must not automatically authorize:

- PID file deletion
- lock deletion
- socket deletion
- stale artifact cleanup
- daemon restart
- lock stealing
- OS service repair

Cleanup remains a separate decision and mutation boundary.

## RDE Delta-M Review

### Preserved

The resident daemon remains staged and auditable.

PID parsing remains explicitly weaker than liveness proof.

### Supplemented

The roadmap now defines process existence as a distinct evidence layer.

### Deviation Risks

Do not treat PID parse success as process existence.

Do not treat process existence as Sayane identity.

Do not treat permission-denied or unsupported probing as process absence.
