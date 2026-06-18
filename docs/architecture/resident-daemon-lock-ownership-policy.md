# Resident Daemon Lock Ownership Policy

Status: Future mutation and concurrency policy

Related issues: #211, #214

## Summary

This document defines the policy for future resident daemon lock ownership.

Locks are concurrency and ownership boundaries. They must not be treated as ordinary stale files or ordinary cleanup artifacts.

Current Sayane resident daemon preview commands do not acquire, release, delete, repair, or steal locks.

## Core rule

Lock operations require stronger evidence and stricter race-safety than ordinary artifact cleanup.

A future command must not delete or steal a lock based only on artifact presence.

## Lock evidence layers

A future lock ownership model should separate:

```text
lock artifact exists
-> lock artifact is well-formed
-> lock owner metadata is readable
-> owner process existence is checked
-> owner process identity is checked
-> lock freshness is checked
-> lock ownership is verified
```

Each layer is stronger than the previous layer.

## Lock acquisition

Future lock acquisition must be atomic.

It must be scoped to the runtime root and must fail closed if ownership is ambiguous.

Requirements:

```text
explicit command intent
atomic acquisition primitive
runtime-root validation
owner metadata write policy
audit record
```

## Lock release

Future lock release must verify that the requester owns the lock or has explicit operator authorization to release it.

Requirements:

```text
owner verification
runtime-root validation
freshness check
audit record
```

A daemon must not release a lock it does not own.

## Stale lock classification

A stale lock is not proven merely by old-looking metadata or artifact presence.

Future stale lock classification should use conservative statuses such as:

```text
lock_missing
lock_present_owner_unverified
lock_owner_process_unverified
lock_owner_identity_unverified
lock_owner_active
lock_owner_stale_unverified
lock_stale_review_required
lock_stale_verified
lock_unsafe_to_steal
manual_review_required
```

No current command should produce `lock_stale_verified`.

## Lock stealing

Lock stealing is high risk.

Future lock stealing requires:

```text
explicit operator intent
stale-owner evidence
process existence evidence
process identity evidence where applicable
race-safety design
audit record
rollback or recovery note
```

Lock stealing must not be folded into generic cleanup.

## Race-safety

Future lock operations must account for races such as:

- daemon starts while cleanup runs
- daemon exits while verification runs
- PID is reused between checks
- lock owner metadata changes between preview and apply
- multiple operator sessions attempt repair

A future implementation must revalidate immediately before mutation.

## Relationship to PID and liveness diagnostics

PID parsing does not prove lock ownership.

Process existence does not prove lock ownership.

Process identity may contribute to lock ownership evidence but is not sufficient unless the lock is scoped and fresh.

## Relationship to cleanup

A lock file is not an ordinary stale artifact.

A cleanup apply command must not delete or steal lock artifacts unless a lock-specific policy and authorization path approves it.

## Relationship to repair

Lock repair is distinct from lock stealing.

Repair may rewrite metadata.

Stealing changes ownership.

Both require explicit policy, operator consent, and audit.

## Audit requirements

Future lock operations must record:

- operation type
- runtime root
- lock path
- prior lock metadata
- owner evidence
- freshness evidence
- operator intent
- mutation performed
- result
- failure mode
- recovery note

## RDE Delta-M Review

### Preserved

Resident daemon concurrency boundaries remain explicit.

Preview commands remain non-mutating.

### Supplemented

The roadmap now treats locks as ownership boundaries rather than cleanup debris.

### Deviation Risks

Do not delete or steal locks based only on artifact presence.

Do not treat PID parse success as lock ownership proof.

Do not combine cleanup, repair, and lock stealing into one convenience command.
