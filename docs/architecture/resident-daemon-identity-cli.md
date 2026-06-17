# Resident Daemon Identity CLI

This document records #192 resident daemon identity CLI preview.

## Status

A read-only daemon identity preview command is implemented.

It does not write PID files, acquire locks, create sockets, or control processes.

## Command

```bash
sayane app daemon-identity --json
```

## Payload

The command returns:

```text
name
runtime_dir
pid_path
lock_path
socket_path
writes_files
acquires_lock
stale_lock_policy
is_process_control
kind
preview_only
```

The payload is derived from `ResidentDaemonIdentity`.

## Runtime directory

By default, the runtime directory is planned under the Sayane home directory:

```text
.sayane/run
```

A custom runtime directory can be supplied:

```bash
sayane app daemon-identity --runtime-dir /path/to/runtime --json
```

## Safety properties

The command is diagnostic only.

It explicitly reports:

```text
writes_files: false
acquires_lock: false
is_process_control: false
preview_only: true
```

## Non-goals

This command does not add:

- PID file writes
- lock acquisition
- socket creation
- process control
- stale lock cleanup
- OS service integration

## RDE Delta-M Review

### Preserved

Process identity remains a plan-only contract.

No hidden daemon process is introduced.

### Supplemented

Operators and future UI code can inspect the planned PID, lock, and socket paths.

### Deviation Risk

Do not treat the identity preview as proof that a daemon is running.

Do not use this command as a process registry.
