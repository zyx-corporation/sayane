# Resident Daemon Preflight Checklist

Status: Schema-only implementation gate preview

## Summary

This document describes the resident daemon implementation gate preflight checklist.

The checklist is exposed through a read-only command:

```bash
sayane app daemon-preflight --json
```

The command does not mutate filesystem state, probe processes, control processes, expose IPC, or integrate with OS services.

## Purpose

The preflight checklist summarizes whether the policy and schema layers required before actual resident daemon implementation are available.

It is not an implementation acceptance record.

It is not permission to start a daemon.

## Aggregate statuses

```text
pass
review_required
blocked
not_applicable
```

The aggregate report status is conservative:

- any `blocked` item makes the report `blocked`
- otherwise any `review_required` item makes the report `review_required`
- otherwise the report is `pass`

## Default checklist items

```text
evidence_ladder_documented
mutation_boundary_documented
operator_consent_documented
ipc_authentication_future_work
process_control_future_work
os_service_integration_deferred
audit_event_schema_available
```

The default report is expected to be `review_required`, because IPC authentication and process control remain future work.

## Safety flags

The report keeps these flags false:

```text
mutates_filesystem: false
probes_process: false
controls_process: false
exposes_ipc: false
integrates_os_service: false
```

## Relationship to implementation readiness gate

The preflight checklist operationalizes the documentation in:

```text
docs/architecture/resident-daemon-implementation-readiness-gate.md
```

It does not replace explicit gate acceptance.

A future implementation issue still needs an explicit acceptance record before actual resident daemon implementation begins.

## RDE Delta-M Review

### Preserved

Resident daemon remains preview-first.

Implementation remains gated.

### Supplemented

The implementation gate now has a machine-readable preflight checklist shape.

### Deviation Risks

Do not treat `review_required` as implementation approval.

Do not use this command to perform runtime initialization or process control.

Do not let the preflight command become an apply command.
