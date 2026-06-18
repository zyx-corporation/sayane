# Resident Daemon Runtime Init Metadata Schema

Status: Minimal implementation slice

## Summary

`daemon-runtime-init --write-metadata` may write a single initialization metadata placeholder
to `state/runtime-init.json`.

This file is initialization-only metadata. It is not daemon liveness, readiness, ownership, or
process identity proof.

## Fields

```text
schema_version
runtime_root
operation_id
creator_surface
write_metadata_requested
confirm_operation_id
confirmation_matched
created_at
disclaimer
```

## Current write boundary

The current implementation may write this metadata only when both are true:

- `--apply`
- `--write-metadata`
- `--confirm-operation-id <operation-id>` matches the plan operation id

Dry-run preview does not write metadata.

## Non-goals retained

This metadata does not:

- claim daemon start
- claim PID ownership
- claim lock ownership
- claim readiness
- claim API reachability
