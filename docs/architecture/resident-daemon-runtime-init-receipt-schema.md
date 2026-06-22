# Resident Daemon Runtime Init Receipt Schema

Status: Minimal implementation slice

## Summary

`daemon-runtime-init --apply` now returns a schema-only apply receipt in the command payload.

This receipt is not persisted automatically. It exists to make the first mutating runtime-init
slice auditable before a later ADR introduces any persistent audit store.

## Fields

```text
schema_version
runtime_root
operation_id
creator_surface
plan_fingerprint
result
applied
created_paths
mutations_performed
metadata_written
failure_mode
recovery_note
metadata_path
confirm_operation_id
confirm_plan_fingerprint
confirmation_matched
fingerprint_matched
created_at
disclaimer
persisted
```

## Current boundary

The receipt:

- is returned in apply payloads only
- is JSON-friendly and schema-only
- does not write itself to disk
- may summarize whether metadata was written during the same apply
- may summarize refused or failed apply outcomes without claiming persistence

## Non-goals retained

This receipt does not:

- persist audit records
- claim daemon start
- claim liveness or readiness
- claim lock ownership
- claim process identity
