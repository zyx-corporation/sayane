# Resident Daemon Implementation Readiness Gate

Status: Transition gate for future implementation

Related issues: #207, #211, #218, #219, #220, #221

## Summary

This document defines the readiness gate for starting actual resident daemon implementation.

The purpose of this gate is to prevent an accidental transition from preview, diagnostic, and policy work into process creation, IPC exposure, filesystem mutation, or OS service integration.

## Current state

The current resident daemon track is preview-first.

Implemented preview and policy layers include:

```text
identity preview
lifecycle preview
operation plan preview
runtime layout preview
filesystem mutation policy
stale artifact diagnostic preview
cleanup decision preview
PID file parse diagnostic preview
liveness proof policy
liveness diagnostic preview
process existence policy
process identity policy
readiness/API readiness policy
mutation authorization policy
cleanup apply policy
artifact repair policy
lock ownership policy
socket lifecycle policy
runtime initialization policy
local IPC authentication policy
operator runbook and consent policy
process control policy
OS service integration policy
```

Actual resident daemon runtime implementation remains future work.

## Gate rule

Actual resident daemon implementation must not begin until this gate is explicitly accepted.

A future implementation issue must state which gate checklist items are satisfied and which remain intentionally deferred.

## Out of scope until gate acceptance

Until the gate is accepted, the following remain out of scope:

- daemon process start
- daemon process stop
- daemon process restart
- signal sending
- process supervision
- PID file writes
- lock acquisition
- lock release
- lock stealing
- socket creation
- IPC endpoint exposure
- runtime directory creation
- stale artifact deletion
- artifact repair
- OS service integration
- persistent IPC credentials
- network-exposed resident API

## Required checklist

Before actual implementation begins, the project should confirm:

### Evidence model

- PID parse validity remains distinct from liveness.
- Process existence remains distinct from process identity.
- Process identity remains distinct from daemon readiness.
- Daemon readiness remains distinct from API readiness.

### Mutation model

- Diagnostics do not authorize mutation.
- Preview and apply commands are separate.
- Cleanup and repair are separate mutation classes.
- Runtime initialization is separate from daemon launch.
- Lock operations are not generic cleanup.
- Socket lifecycle is not generic cleanup.

### Operator model

- Apply/control/service commands require explicit operator intent.
- Preview hash or operation id is defined for mutating operations.
- Evidence revalidation is required before mutation.
- Audit records are required for mutation and process control.
- Conservative failures are explained without overclaiming safety.

### IPC model

- Local-only default is preserved.
- Endpoint reachability is not authentication.
- Authentication is not authorization.
- Authorization is not operation readiness.
- Capability binding is defined before resident API exposure.

### Process model

- Start, stop, restart, signal, and supervision are separated.
- Process identity is required before stop/signal behavior.
- Runtime initialization does not launch a daemon.
- OS service integration is platform-specific and separate.

### Release model

- Local checks are defined.
- CI must pass.
- Release notes must preserve non-goal boundaries.
- RDE review must confirm no preview command became mutating.

## Minimum first implementation shape

The first actual resident daemon implementation should be minimal.

Recommended first implementation constraints:

```text
local-only
single-user
no OS service integration
no network exposure
no cleanup apply
no repair apply
no lock stealing
no auto-start
no persistent IPC credentials
explicit operator start only
```

## RDE review required before implementation

Before implementation begins, RDE review should verify:

### Preserved

- preview-first design
- local-first boundary
- non-mutating diagnostics
- explicit operator consent
- evidence ladder

### Transformed

- policy artifacts become implementation constraints
- diagnostic previews become possible preflight checks

### Supplemented

- runtime state machine
- IPC handshake implementation
- audit event schema
- failure recovery behavior

### Unresolved

- exact daemon state machine
- exact IPC transport
- credential lifetime
- platform support matrix
- packaging and service integration timeline

### Deviation risks

- preview command becomes mutating
- daemon launch happens as side effect
- PID write becomes false liveness claim
- socket reachability becomes false API readiness claim
- automation bypasses operator consent

## Acceptance record

A future issue that opens implementation should include an acceptance record:

```text
implementation_gate: accepted
accepted_by: <operator or maintainer>
accepted_at: <timestamp>
scope: <minimal implementation scope>
explicit_non_goals: <non-goals retained>
```

## RDE Delta-M Review

### Preserved

The preview-first strategy remains explicit.

The resident daemon remains unimplemented until a gate is accepted.

### Supplemented

The roadmap now has a transition boundary from policy/preview work to runtime implementation.

### Deviation Risks

Do not slide from diagnostics into daemon runtime behavior.

Do not treat policy completeness as implementation authorization.

Do not omit an explicit implementation acceptance record.
