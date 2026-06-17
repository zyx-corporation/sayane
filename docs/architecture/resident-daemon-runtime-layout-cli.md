# Resident Daemon Runtime Layout CLI

This document records #196 resident daemon runtime layout CLI preview.

## Status

A read-only daemon runtime layout preview command is implemented.

It does not create directories, write files, acquire locks, or control processes.

## Command

```bash
sayane app daemon-runtime-layout --json
```

## Payload

The command returns:

```text
runtime_root
pid_dir
lock_dir
socket_dir
log_dir
temp_dir
state_dir
creates_directories
writes_files
is_filesystem_mutation
kind
preview_only
```

The payload is derived from `ResidentDaemonRuntimeLayout`.

## Runtime root

By default, the runtime root is planned under the Sayane home directory:

```text
.sayane/run
```

A custom runtime root can be supplied:

```bash
sayane app daemon-runtime-layout --runtime-root /path/to/runtime --json
```

## Safety properties

The command is diagnostic only.

It explicitly reports:

```text
creates_directories: false
writes_files: false
is_filesystem_mutation: false
preview_only: true
```

## Non-goals

This command does not add:

- directory creation
- PID file writes
- lock file writes
- socket creation
- log writes
- temp file creation
- state file persistence
- stale file cleanup
- process control
- OS service integration

## RDE Delta-M Review

### Preserved

Runtime layout remains a plan-only contract.

No filesystem mutation or hidden daemon process is introduced.

### Supplemented

Operators and future UI code can inspect the planned resident runtime directory layout.

### Deviation Risk

Do not treat the runtime layout preview as proof that runtime directories exist.

Do not use this command as a runtime state registry.
