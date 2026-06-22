# Resident Daemon Runtime Init Command

Status: Minimal implementation slice

## Summary

`sayane app daemon-runtime-init` is the first resident daemon filesystem mutation surface.

It is intentionally limited to explicit creation of an empty runtime root and its planned
subdirectories.

## Command shapes

Preview:

```bash
sayane app daemon-runtime-init --json
```

Apply:

```bash
sayane app daemon-runtime-init --apply --json
```

Explicit operation id:

```bash
sayane app daemon-runtime-init --operation-id init-001 --apply --json
```

## Current scope

This command may create only:

- runtime root
- `pid/`
- `lock/`
- `socket/`
- `log/`
- `tmp/`
- `state/`

## Non-goals retained

This command does not:

- write PID files
- write readiness metadata
- acquire locks
- create sockets
- start a daemon
- stop a daemon
- repair artifacts
- delete stale artifacts
- integrate with OS services

Metadata placeholder writes are allowed only with explicit `--write-metadata` during apply.
Metadata placeholder writes also require matching `--confirm-operation-id <operation-id>`.
Metadata placeholder writes also require matching `--confirm-plan-fingerprint <fingerprint>`.

## Failure boundary

Apply fails closed when a target path already exists as a non-directory or symlink.

Preview remains non-mutating and reports `manual_review_required` when apply would be unsafe.

## Audit-ready payload

Current preview/apply payloads include:

- `operation_id`
- `plan_fingerprint`
- `creator_surface`
- `target_paths`
- `prior_state`
- `proposed_state`
- `operator_confirmation_signal`
- `mutations_performed`
- `result`

Apply payloads also include a schema-only `resident_daemon_runtime_init_receipt` with:

- `operation_id`
- `plan_fingerprint`
- `created_paths`
- `mutations_performed`
- `metadata_written`
- `confirm_operation_id`
- `confirm_plan_fingerprint`
- `failure_mode`
- `recovery_note`

When requested with `--include-event-record`, preview/apply payloads also include a derived
`resident_daemon_event_record` using:

- `preview` category for dry-run
- `apply` category for explicit apply
- consent evidence for metadata write confirmation state

When requested with `--write-metadata`, apply payloads also include:

- `metadata_written`
- `metadata_path`
- `metadata`
- `confirm_operation_id`
- `confirm_plan_fingerprint`
- `confirmation_matched`
- `fingerprint_matched`

The receipt is not persistent audit storage and must not be interpreted as daemon liveness,
readiness, ownership, or process identity proof.

When `--apply --json` is used and apply is refused or fails closed, the command returns the same
apply-shaped payload with:

- `applied: false`
- `result: requires_review | aborted | failed`
- `failure_mode`
- optional `event_record`
- `receipt`
