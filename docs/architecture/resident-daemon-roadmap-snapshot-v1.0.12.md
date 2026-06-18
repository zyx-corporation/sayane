# Resident Daemon Roadmap Snapshot for v1.0.12

Status: Roadmap snapshot

Related issues: #198-#222

## Summary

This snapshot records the resident daemon roadmap state at the v1.0.12 policy gate.

Sayane has not implemented a production resident daemon. The project has instead established a preview-first evidence, mutation, IPC, operator consent, and implementation readiness policy stack.

## Completed preview and policy layers

```text
Foundation
├─ resident app service boundary
├─ runtime repository selection
├─ local capability policy
├─ daemon identity preview
├─ daemon lifecycle preview
├─ daemon operation plan preview
├─ daemon runtime layout preview
├─ filesystem mutation policy
├─ stale artifact diagnostic preview
├─ cleanup decision preview
├─ PID file parse diagnostic preview
├─ liveness proof policy
├─ liveness diagnostic preview
├─ process existence policy
├─ process identity policy
├─ readiness / API readiness policy
├─ mutation authorization policy
├─ cleanup apply command policy
├─ artifact repair policy
├─ lock ownership policy
├─ socket lifecycle policy
├─ runtime initialization policy
├─ local IPC authentication policy
├─ operator runbook and consent policy
├─ process control policy
├─ OS service integration policy
└─ implementation readiness gate
```

## Current evidence ladder

```text
PID parse validity
    ↓
process existence
    ↓
process identity
    ↓
daemon readiness
    ↓
API readiness
```

Only preview and policy layers exist today. Process existence verification, process identity verification, readiness verification, and API readiness verification remain future work.

## Current mutation ladder

```text
diagnostic evidence
    ↓
decision preview
    ↓
operator authorization
    ↓
mutation or control command
    ↓
audit record
```

Only diagnostics, decision previews, and policies exist today. Mutation and control commands remain future work.

## Current safety boundary

The resident daemon track still does not include:

- production resident daemon runtime
- daemon process start
- daemon process stop
- daemon process restart
- signal sending
- process supervision
- process probing
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

## Active preview commands

```bash
sayane app daemon-identity --json
sayane app daemon-plan --json
sayane app daemon-start-plan --json
sayane app daemon-stop-plan --json
sayane app daemon-restart-plan --json
sayane app daemon-runtime-layout --json
sayane app daemon-stale-artifacts --json
sayane app daemon-cleanup-decisions --json
sayane app daemon-pid-diagnostic --json
sayane app daemon-liveness-diagnostic --json
```

## Implementation gate

Actual resident daemon implementation should not begin until a future implementation issue explicitly accepts the implementation readiness gate.

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

## Remaining future work

```text
Runtime Implementation
├─ minimal daemon state machine
├─ explicit operator start command
├─ PID write implementation
├─ atomic lock acquisition implementation
├─ local IPC transport choice
├─ authenticated local IPC handshake
├─ readiness reporting
├─ audit event schema
└─ failure recovery behavior

Post-MVP Work
├─ cleanup apply implementation
├─ repair apply implementation
├─ lock stealing implementation, if ever approved
├─ socket replacement implementation
├─ OS service integration
├─ persistent IPC credentials
└─ network-exposed API, if ever approved
```

## RDE Delta-M Review

### Preserved

The resident daemon remains preview-first and non-mutating.

Implementation remains gated.

### Supplemented

The roadmap now records a coherent transition path from evidence and policy to future runtime implementation.

### Deviation Risks

Do not treat this roadmap snapshot as implementation authorization.

Do not treat policy completion as process-control permission.

Do not collapse diagnostics, mutation, IPC, and OS integration into one implementation step.
