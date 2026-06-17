# Resident Daemon Lifecycle

This document records #187 resident daemon lifecycle design.

## Status

A lifecycle contract model is implemented.

This is not a running resident daemon implementation.

## States

The lifecycle model defines these states:

```text
stopped
starting
running
stopping
failed
```

Allowed transitions are intentionally narrow:

```text
stopped  -> starting | failed
starting -> running | stopping | failed
running  -> stopping | failed
stopping -> stopped | failed
failed   -> stopped | starting
```

## Modes

The lifecycle model defines two ownership modes:

```text
bridge_delegation
resident_server_reserved
```

`bridge_delegation` is the current mode. It means resident app commands still delegate serving to the existing Bridge server path.

`resident_server_reserved` is a future placeholder. It does not start a new resident server.

## Local bind policy

A future resident daemon must bind only to localhost addresses:

```text
127.0.0.1
localhost
::1
```

Non-local bind addresses such as `0.0.0.0` are rejected by the lifecycle contract.

## Current command relationship

`sumane app serve` remains a delegation plan to the existing Bridge command until a real daemon server is implemented.

```text
sayane app serve --host 127.0.0.1 --port 38741
  -> sayane serve --host 127.0.0.1 --port 38741
```

The lifecycle model records this relationship, but does not start processes.

## Credential and unlock policy

The lifecycle model records these fields as explicit future seams:

```text
runtime_backend
unlock_session_binding
capability_policy
```

Defaults remain conservative:

```text
runtime_backend: legacy_process_local
unlock_session_binding: unbound
capability_policy: local_development
```

## Non-goals

This design does not add:

- OS service installation
- systemd, launchd, or Windows Service support
- new HTTP server ownership
- production authentication
- durable capability tokens
- vault unlock-session implementation
- pro backend implementation

## RDE Delta-M Review

### Preserved

Resident app remains an application/runtime boundary.

Bridge remains canonical for serving until daemon ownership is explicitly implemented.

Capability policy remains local-only and non-persistent.

### Transformed

Daemon lifecycle is now a testable contract rather than an implicit future idea.

### Supplemented

Local bind policy, state transitions, and restart-from-failure behavior are now explicit.

### Unresolved

Real process lifecycle, service installation, unlock-session binding, and production credentials remain future work.

### Deviation Risk

Do not present this lifecycle contract as a production resident daemon.

Do not add a second HTTP server path without revisiting Bridge ownership and authentication.
