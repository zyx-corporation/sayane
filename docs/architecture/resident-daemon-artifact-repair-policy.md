# Resident Daemon Artifact Repair Policy

Status: Future mutation policy

Related issues: #211, #212, #213

## Summary

This document defines the policy for any future resident daemon artifact repair command.

Repair is distinct from cleanup. Cleanup removes artifacts. Repair creates, rewrites, normalizes, or restores artifacts.

Current Sayane resident daemon preview commands do not repair artifacts.

## Core rule

Repair must never be hidden behind diagnostics or cleanup preview commands.

A future repair command must have:

- explicit command naming
- explicit operator intent
- evidence thresholds
- runtime-root validation
- audit record
- failure and recovery behavior

## Repair vs cleanup

Cleanup:

```text
remove an artifact judged safe to remove
```

Repair:

```text
create, rewrite, normalize, or restore an artifact
```

These operations have different risks.

A cleanup command must not silently repair.

A repair command must not silently cleanup unrelated artifacts.

## Repair classes

### Class R0: No-op repair preview

Examples:

- show proposed repair
- explain why repair is unsafe
- classify missing metadata

Authorization:

```text
read-only preview only
```

### Class R1: Runtime directory creation

Examples:

- create runtime root
- create planned runtime subdirectories

Requirements:

```text
explicit operator intent
runtime-root validation
path escape rejection
no conflicting existing artifact
audit record
```

### Class R2: Metadata creation

Examples:

- create daemon metadata file
- create state metadata
- create readiness metadata

Requirements:

```text
explicit operator intent
runtime-root validation
schema validation
freshness metadata
audit record
```

Metadata creation must not imply daemon liveness.

### Class R3: Metadata rewrite

Examples:

- rewrite malformed metadata
- update stale schema metadata
- normalize state metadata

Requirements:

```text
explicit operator intent
backup or recovery note
schema validation
old and new value audit
manual review for ambiguity
```

### Class R4: PID file repair

Examples:

- rewrite PID file
- delete-and-recreate PID file
- normalize PID file content

Requirements:

```text
explicit operator intent
process identity or launch ownership evidence
runtime-root validation
freshness evidence
audit record
```

A PID file repair can create false liveness authority and must be treated as high risk.

### Class R5: Lock metadata repair

Examples:

- rewrite lock metadata
- normalize lock owner data
- replace stale lock metadata

Requirements:

```text
explicit operator intent
lock ownership policy
race-safety design
process existence and identity evidence where applicable
audit record
```

Lock metadata repair must not steal locks implicitly.

### Class R6: Socket artifact repair

Examples:

- recreate socket artifact
- replace stale socket file
- normalize socket metadata

Requirements:

```text
explicit operator intent
socket lifecycle policy
local IPC policy
authentication policy
audit record
```

Socket repair may create or expose communication surfaces and must remain separate from cleanup.

## Future command naming

Future repair commands should use explicit mutating names, such as:

```bash
sayane app daemon-runtime-repair-apply
sayane app daemon-metadata-repair-apply
sayane app daemon-pid-repair-apply
```

Diagnostic, preview, and plan commands must not repair.

## Operator consent

Future repair commands should require explicit confirmation, such as:

```text
--apply
--operation-id <id>
--confirm <preview-hash>
interactive typed confirmation
signed local approval
```

Repair must revalidate evidence immediately before mutation.

## Audit requirements

Future repair commands must record:

- repair class
- runtime root
- target artifact path
- old artifact state
- proposed new state
- evidence inputs
- operator confirmation
- mutation performed
- result
- rollback or recovery note

## Failure behavior

Repair must fail closed when:

- runtime root validation fails
- target path escapes runtime root
- artifact type is unexpected
- evidence changes between preview and apply
- ownership is ambiguous
- process identity is unverified where required
- platform behavior is unsupported
- permissions are insufficient

## RDE Delta-M Review

### Preserved

Preview commands remain non-mutating.

Cleanup and repair remain separate concepts.

### Supplemented

The roadmap now has a repair-specific policy for future mutating commands.

### Deviation Risks

Do not let cleanup apply silently repair artifacts.

Do not let diagnostics rewrite files.

Do not let PID repair imply liveness proof.
