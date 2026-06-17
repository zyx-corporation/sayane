# Resident Daemon PID File Diagnostics

This document records #202 resident daemon PID file parse diagnostic preview.

## Status

Read-only diagnostic preview.

No process liveness probing, process control, or filesystem mutation is introduced.

## Purpose

The resident daemon preview sequence can now observe planned runtime artifacts and produce cleanup decisions.

The next safe diagnostic layer is PID file parsing.

This layer answers:

```text
If a planned PID file exists, can its content be parsed as a positive integer PID?
```

It does not answer:

```text
Is that process alive?
Is that process Sayane?
Is that process owned by the current user?
Is it safe to delete the PID file?
```

Those checks remain future work.

## Command

```bash
sayane app daemon-pid-diagnostic --json
```

Optional runtime root override:

```bash
sayane app daemon-pid-diagnostic --runtime-root /path/to/runtime --json
```

## Status values

The diagnostic reports one of:

```text
missing
unreadable
empty
invalid
parsed
```

## Current behavior

### Missing PID file

```text
missing -> manual_review_required: false
```

A missing PID file is expected before a real resident daemon exists.

### Existing PID file

Existing PID file states are conservative:

```text
unreadable -> manual_review_required: true
empty -> manual_review_required: true
invalid -> manual_review_required: true
parsed -> manual_review_required: true
```

A parsed PID is only parsed text.

It is not proof of process liveness.

## Payload

The payload includes:

```text
kind
preview_only
path
exists
status
parsed_pid
raw_value_preview
error
manual_review_required
proves_liveness
probes_process
controls_process
mutates_filesystem
```

The following remain false:

```text
proves_liveness: false
probes_process: false
controls_process: false
mutates_filesystem: false
```

## Safety boundary

This preview does not:

- create PID files
- delete PID files
- repair PID files
- acquire locks
- create sockets
- send signals
- start daemon processes
- stop daemon processes
- assert process liveness

## Relationship to prior work

```text
#198 filesystem mutation policy
#199 stale artifact diagnostic preview
#200 cleanup decision preview
#202 PID file parse diagnostic preview
```

The sequence remains:

```text
observation -> decision -> mutation
```

Only observation and decision exist today.

## RDE Delta-M Review

### Preserved

Preview commands remain non-mutating.

PID file existence is not treated as daemon liveness.

Manual review remains the default for ambiguity.

### Supplemented

The system can now distinguish missing, empty, invalid, unreadable, and parsed PID file content.

This prepares a future process identity verification step without introducing process control.

### Deviation Risks

Do not treat a parsed PID as proof that a daemon is alive.

Do not treat a parsed PID as proof that the process is Sayane.

Do not delete or repair PID files from this preview.

Do not add signal-based process checks to this preview command.
