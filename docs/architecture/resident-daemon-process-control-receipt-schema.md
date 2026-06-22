# Resident Daemon Process Control Receipt Schema

Status: MVP implementation slice

## Summary

`daemon-start`, `daemon-stop`, and `daemon-restart` return a structured process-control receipt.

The receipt captures the local operation result before any future persistent resident audit store
exists.

## Fields

```text
operation
operation_id
runtime_root
host
port
state_before
state_after
result
applied
pid_path
lock_path
log_path
health_url
pid
failure_mode
recovery_note
command
manual_review_required
created_at
```

## Current boundary

The receipt:

- is returned directly in command payloads
- is local-only and non-persistent
- may include a derived `resident_daemon_event_record`
- must not be treated as OS-service state or cross-host authority
