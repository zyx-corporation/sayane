# Resident Daemon Event Record Schema

Status: Schema-only implementation support

## Summary

This document describes the resident daemon event record schema added after the v1.0.12 implementation readiness gate.

The schema provides a common JSON-friendly shape for future preview, apply, process, IPC, and service operation records.

It does not persist events, write audit logs, mutate filesystem state, control processes, expose IPC, or integrate with OS services.

## Event categories

```text
preview
apply
process
ipc
service
```

`preview` records are for non-mutating preview surfaces.

`apply`, `process`, `ipc`, and `service` are future operation categories. Their presence in the schema does not implement those operations.

## Event results

```text
planned
succeeded
failed
aborted
requires_review
```

The initial default is `planned`.

## Safety flags

The schema records explicit side-effect flags:

```text
mutates_filesystem
controls_process
exposes_ipc
integrates_os_service
```

Preview records must not set any of these flags.

Every record also reports:

```text
persisted: false
```

because this schema does not write records anywhere.

## Required fields

```text
operation_id
category
surface
result
```

`operation_id` and `surface` must not be empty.

## Optional fields

```text
runtime_root
evidence
consent
message
```

These fields are non-sensitive summaries intended for local diagnostics and future auditability.

## Relationship to future audit persistence

This schema is not an audit store.

Future audit persistence must define:

- storage location
- retention policy
- privacy boundary
- tamper evidence if needed
- export format
- redaction rules
- failure behavior

## Relationship to preview commands

Preview commands may use this schema in the future to describe what they observed or planned.

A preview event must remain non-mutating.

## Relationship to future operation commands

Future operation commands may use this schema as the base for local audit records, but must still define their own authorization, evidence, revalidation, and persistence behavior.

## RDE Delta-M Review

### Preserved

Resident daemon remains preview-first.

No process behavior, IPC behavior, or filesystem mutation is introduced.

### Supplemented

Future operation auditability now has a concrete event shape.

### Deviation Risks

Do not treat schema creation as audit persistence.

Do not treat future operation categories as implemented capabilities.

Do not allow preview records to carry side-effect flags.
