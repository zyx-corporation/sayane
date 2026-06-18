# Resident Daemon Mutation Authorization Policy

Status: Future mutation policy

Related issues: #198, #200, #211

## Summary

This document defines the authorization policy for any future resident daemon filesystem mutation.

Current resident daemon work remains read-only and preview-only. Diagnostics and decision previews may describe evidence, risk, and possible operator choices, but they must not mutate filesystem artifacts or control processes.

## Core rule

Diagnostics never automatically authorize mutation.

A diagnostic result is evidence. It is not permission.

A cleanup decision preview is a recommendation. It is not execution authority.

A future mutation command must require its own explicit operator intent, evidence threshold, and audit record.

## Current non-mutating boundary

Current resident daemon commands do not:

- start a daemon
- stop a daemon
- restart a daemon
- supervise a daemon
- probe a process
- control a process
- write PID files
- repair PID files
- delete PID files
- acquire locks
- steal locks
- create sockets
- delete sockets
- create runtime directories
- delete stale artifacts
- repair stale artifacts
- integrate with OS service managers
- expose a network-resident API

This boundary remains in force until a separate future mutation command is designed and explicitly accepted.

## Mutation classes

Future mutation work should classify operations before implementation.

### Class 0: Read-only observation

Examples:

- inspect planned paths
- parse PID file content
- classify artifact presence
- classify type mismatch
- report liveness evidence ceiling

Authorization requirement:

```text
no mutation authorization required
```

Current preview commands are Class 0.

### Class 1: Safe local creation under empty runtime root

Examples:

- create missing runtime root
- create missing runtime subdirectories
- create empty log directory

Authorization requirement:

```text
explicit operator intent
runtime-root validation
no conflicting existing artifact
```

Even apparently safe creation must not be performed by diagnostic commands.

### Class 2: Metadata write

Examples:

- write PID file
- write daemon metadata
- write readiness metadata
- write state metadata

Authorization requirement:

```text
explicit operator intent
runtime-root validation
process identity or launch ownership evidence
freshness evidence
audit record
```

Metadata writes can create false authority if stale or incorrect, so they require stronger control boundaries.

### Class 3: Cleanup or repair of stale artifacts

Examples:

- delete stale PID file
- delete stale lock file
- delete stale socket file
- repair type-mismatched artifact path
- remove obsolete runtime metadata

Authorization requirement:

```text
explicit operator intent
artifact-specific evidence
manual review for ambiguity
no active owner evidence
audit record
rollback or recovery note when possible
```

No existing decision currently marks an artifact safe for automatic deletion.

### Class 4: Lock acquisition or lock stealing

Examples:

- acquire resident daemon lock
- break stale lock
- replace lock owner metadata

Authorization requirement:

```text
explicit operator intent
process existence check
process identity check where applicable
stale-owner evidence
race-safety design
audit record
```

Lock stealing is always high risk and must not be hidden inside cleanup.

### Class 5: Socket creation or replacement

Examples:

- create local IPC socket
- replace stale socket artifact
- bind resident API endpoint

Authorization requirement:

```text
explicit operator intent
runtime-root validation
process identity or launch ownership evidence
local-only binding policy
authentication policy
audit record
```

Socket presence is not identity proof and socket creation may expose a communication surface.

### Class 6: Process control

Examples:

- start daemon
- stop daemon
- restart daemon
- signal daemon
- supervise daemon

Authorization requirement:

```text
explicit operator intent
process identity policy
readiness policy
failure recovery policy
operator-visible effect summary
audit record
```

Process control is outside current preview scope.

### Class 7: OS service integration

Examples:

- install service file
- update launch agent
- enable systemd unit
- register Windows service

Authorization requirement:

```text
explicit operator intent
platform-specific policy
privilege boundary policy
rollback plan
audit record
```

OS service integration is outside current preview scope.

## Operator consent model

Future mutation commands must require explicit operator intent.

Acceptable future consent patterns may include:

```text
--apply
--confirm <operation-id>
--yes after preview hash
interactive typed confirmation
signed local operation approval
```

A diagnostic command name must not become mutating by adding an option casually.

Preferred pattern:

```text
preview command -> separate apply command
```

not:

```text
preview command --fix
```

unless a future policy explicitly approves that design.

## Evidence thresholds

Mutation authorization should depend on evidence strength.

Examples:

```text
missing artifact + explicit create command -> may create
parsed PID only -> may not delete or signal
process exists but identity unverified -> may not signal or repair ownership
identity verified but readiness unknown -> may not assume API readiness
ambiguous stale artifact -> manual_review_required
```

Weak evidence must produce conservative outcomes.

## Audit requirements

Future mutation commands must emit an audit record containing:

- operation class
- operator intent signal
- runtime root
- artifact path or process target
- evidence inputs
- decision result
- mutation performed
- mutation result
- failure mode if applicable
- rollback or recovery note when applicable

Audit should be local-first and suitable for later RDE review.

## Naming policy

Preview commands must remain preview commands.

Future mutating commands should use explicit names that communicate action, such as:

```text
daemon-runtime-init
daemon-artifact-cleanup-apply
daemon-lock-acquire
daemon-start
daemon-stop
```

A command named `diagnostic`, `preview`, or `plan` must not mutate.

## Relationship to cleanup decisions

The current cleanup decision model maps diagnostics conservatively:

```text
missing -> no_action
present_review_required -> manual_review_required
type_mismatch_review_required -> unsafe_to_delete
```

These decisions do not delete or repair artifacts.

A future cleanup apply command must have a separate authorization policy and must not treat existing preview decisions as automatic execution permission.

## RDE Delta-M Review

### Preserved

Resident daemon work remains staged and auditable.

Diagnostics remain non-mutating.

Manual review remains required for ambiguity.

### Supplemented

The roadmap now has an explicit authorization layer between evidence and action:

```text
diagnostic evidence -> decision preview -> operator authorization -> mutation command -> audit record
```

### Deviation Risks

Do not let diagnostic confidence drift into mutation permission.

Do not add `--fix` to preview commands without a separate policy decision.

Do not allow cleanup, repair, lock stealing, socket creation, or process control to bypass explicit operator consent.
