# Resident Daemon Operator Runbook and Consent Policy

Status: Future operator governance policy

Related issues: #211, #212, #216, #217, #218

## Summary

This document defines the operator runbook and consent policy for future resident daemon operations.

The policy consolidates the human authorization boundary before Sayane introduces runtime initialization, repair, cleanup apply, lock operations, socket lifecycle operations, IPC surfaces, process control, or OS service integration.

## Core rule

Preview commands must not mutate.

Apply commands must require explicit operator consent.

High-risk operations must not be hidden behind convenience flags or automation defaults.

## Command classes

Future resident daemon commands should be classified by operator-visible effect.

### Preview commands

Preview commands inspect, classify, or plan.

They must not mutate.

Examples:

```text
daemon-runtime-layout
daemon-stale-artifacts
daemon-cleanup-decisions
daemon-pid-diagnostic
daemon-liveness-diagnostic
```

### Apply commands

Apply commands mutate local state.

They must require explicit consent, evidence revalidation, and audit records.

Examples:

```text
daemon-runtime-init-apply
daemon-cleanup-apply
daemon-repair-apply
```

### Control commands

Control commands affect processes.

They require separate process identity, readiness, failure recovery, and audit policies.

Examples:

```text
daemon-start
daemon-stop
daemon-restart
```

These commands now exist for the local-only MVP control line, but they still require separate
process identity, readiness, failure recovery, and audit policy interpretation. They are not OS
service integration.

### Service commands

Service commands integrate with OS service managers.

They require platform-specific policy and rollback plans.

Examples:

```text
daemon-service-install
daemon-service-enable
daemon-service-disable
```

These commands remain future work.

## Preview/apply convention

Preferred future flow:

```text
preview -> operator review -> apply with preview hash or operation id -> revalidate -> mutate -> audit
```

Avoid:

```text
preview --fix
```

unless a future policy explicitly justifies it.

## Consent mechanisms

Acceptable future consent mechanisms may include:

```text
--apply
--operation-id <id>
--confirm <preview-hash>
interactive typed confirmation
signed local approval
```

High-risk operations should require stronger confirmation than low-risk initialization.

## Evidence revalidation

Apply commands must revalidate evidence immediately before mutation.

They must abort if:

- preview state is stale
- runtime root changed
- artifact changed
- ownership changed
- process identity is ambiguous
- readiness state is incompatible
- permissions are insufficient
- platform behavior is unsupported

## Audit requirements

Future apply/control/service commands must emit local audit records containing:

- command class
- command name
- operation id
- runtime root
- target artifacts or process
- evidence inputs
- consent signal
- mutation or control attempted
- result
- failure mode
- recovery note
- rollback note where applicable

## Operator messaging

Future commands must explain conservative failures clearly.

Examples:

```text
manual_review_required
permission_denied_not_absence
identity_unverified_not_safe_to_mutate
preview_hash_mismatch
runtime_root_mismatch
operation_not_ready
```

Messages must not overclaim safety.

## Automation boundary

Automation must not bypass operator consent for high-risk operations.

Recurring or scripted workflows may run preview commands, but apply/control/service commands require explicit consent unless a separate future policy defines a safe delegated approval mechanism.

Passive supervision reads may be exposed in local app or CLI surfaces, but they must not silently
upgrade into background control or OS service automation.

Recovery guidance may also be exposed in local app or CLI surfaces, but confirmation-bearing cleanup,
repair, and other mutating steps must remain explicit operator actions.

## Recovery notes

Future mutating commands should include recovery guidance when possible.

Examples:

- what was changed
- what was not changed
- how to inspect audit record
- how to restore from backup when available
- what manual review is required

## RDE Delta-M Review

### Preserved

Human authorization remains explicit.

Preview commands remain non-mutating.

### Supplemented

The roadmap now has an operator-facing governance layer connecting preview, evidence, consent, mutation, and audit.

### Deviation Risks

Do not hide mutation behind convenience flags.

Do not let automation bypass consent for high-risk operations.

Do not let operator messaging imply stronger proof than evidence supports.
