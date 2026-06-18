# Resident Daemon State Machine Schema

Status: Schema-only implementation support

## Summary

This document describes the resident daemon state machine schema.

The schema defines a machine-readable set of daemon states and transitions for a future implementation.

It does not start or stop processes, write PID files, create sockets, or mutate runtime state.

## States

```text
stopped
starting
running
stopping
failed
```

The default initial state is:

```text
stopped
```

The default terminal states are:

```text
stopped
failed
```

## Default transitions

```text
request_start
startup_succeeds
request_stop
stop_completes
startup_fails
runtime_fails
recover_after_failure
```

These transitions are schema-only descriptions of future behavior.

They do not execute anything.

## Safety flags

The schema keeps these flags false:

```text
mutates_filesystem: false
controls_process: false
writes_pid_file: false
creates_socket: false
creates_runtime_directory: false
schema_only: true
```

## Relationship to lifecycle contract

The lifecycle contract describes currently recognized daemon lifecycle states and delegation boundaries.

The state machine schema complements that contract by naming future transition edges and triggers.

Neither document implements daemon behavior.

## Relationship to preflight and event records

The preflight checklist explains whether implementation prerequisites are documented.

The event record schema explains how future preview or operation events may be represented.

The state machine schema adds a third layer: the future runtime transition shape.

Together these remain implementation support only.

## Non-goals

This schema does not add:

- process start
- process stop
- process restart
- PID writes
- lock acquisition
- socket creation
- runtime directory creation
- readiness probing
- IPC transport
- audit persistence

## RDE Delta-M Review

### Preserved

Resident daemon remains preview-first and non-operational.

### Supplemented

Future runtime transitions now have a concrete machine-readable shape.

### Deviation Risks

Do not treat this schema as an implemented daemon controller.

Do not attach filesystem or process side effects to this schema-only layer.
