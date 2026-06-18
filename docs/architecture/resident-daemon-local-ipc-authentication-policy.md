# Resident Daemon Local IPC Authentication Policy

Status: Future IPC security policy

Related issues: #210, #215, #217

## Summary

This document defines the policy for future resident daemon local IPC authentication.

Current Sayane resident daemon preview work does not create IPC endpoints, expose resident APIs, start daemon processes, or introduce persistent IPC credentials.

## Core rule

Endpoint reachability is not authentication.

Authentication is not authorization.

Authorization is not operation readiness.

A future local IPC surface must prove each layer explicitly.

## Evidence layers

Future local IPC readiness should be modeled as:

```text
endpoint exists
-> endpoint reachable
-> endpoint authenticated
-> caller authorized
-> protocol compatible
-> operation class ready
```

No current command reaches any of these layers beyond planned socket path diagnostics.

## Local-only default

Future resident IPC must be local-only by default.

Acceptable future local transports may include:

- Unix domain socket on Unix-like systems
- named pipe on Windows
- localhost-bound loopback endpoint only if separately approved

A network-exposed resident API requires separate policy and must not be introduced through local IPC work.

## Runtime-root scoping

Authentication must bind the endpoint to the expected runtime root.

A valid endpoint for one runtime root must not authenticate another runtime root.

Future handshake metadata should include:

- runtime root identifier
- daemon instance identifier
- protocol version
- freshness data
- supported operation classes

## Freshness and replay resistance

Future authentication must defend against stale or replayed evidence.

Possible future mechanisms include:

- nonce challenge
- short-lived local token
- session epoch
- signed local metadata
- capability-bound handshake

No current Sayane command implements these mechanisms.

## Capability binding

Future IPC authorization should bind requests to capability scopes.

Example future surfaces:

```text
capture
review_queue
mcp_preview
admin_diagnostic
admin_mutation
```

A caller authorized for diagnostics must not automatically be authorized for mutation.

## Persistent credentials

Persistent IPC credentials are out of scope for the current resident daemon preview track.

A future credential persistence design must define:

- storage location
- lifetime
- rotation
- revocation
- local user boundary
- unlock-session binding if applicable
- audit behavior

## Conservative future statuses

Future IPC diagnostics should use conservative statuses such as:

```text
ipc_unimplemented
endpoint_missing
endpoint_reachable_auth_unverified
endpoint_auth_failed
endpoint_authenticated_authorization_unverified
endpoint_unauthorized
endpoint_authorized_protocol_mismatch
endpoint_authorized_operation_not_ready
endpoint_api_ready
manual_review_required
```

No current command should claim `endpoint_api_ready`.

## Relationship to socket lifecycle

Socket presence is not authentication.

Endpoint reachability is not authentication.

Socket creation and IPC authentication must remain separate policy layers.

## Relationship to readiness

A daemon may be live and identified but not ready for a specific IPC operation class.

A future IPC handshake must report operation-class readiness, not generic readiness alone.

## Audit requirements

Future authenticated IPC operations must record:

- endpoint identity
- runtime root
- caller surface
- requested capability scope
- authorization result
- protocol version
- operation class
- denial reason where applicable
- mutation class if applicable

## RDE Delta-M Review

### Preserved

Local IPC remains future work.

Current preview commands remain non-exposed and non-mutating.

### Supplemented

The roadmap now defines the authentication and authorization boundary required before resident API implementation.

### Deviation Risks

Do not treat socket reachability as authentication.

Do not treat authentication as authorization.

Do not grant mutation authority through diagnostic capability.

Do not introduce network exposure through local IPC work.
