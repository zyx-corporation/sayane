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

## Failure boundary

Apply fails closed when a target path already exists as a non-directory or symlink.

Preview remains non-mutating and reports `manual_review_required` when apply would be unsafe.

## Audit-ready payload

Current preview/apply payloads include:

- `operation_id`
- `creator_surface`
- `target_paths`
- `prior_state`
- `proposed_state`
- `operator_confirmation_signal`
- `mutations_performed`
- `result`

When requested with `--include-event-record`, preview/apply payloads also include a derived
`resident_daemon_event_record` using:

- `preview` category for dry-run
- `apply` category for explicit apply

When requested with `--write-metadata`, apply payloads also include:

- `metadata_written`
- `metadata_path`
- `metadata`
