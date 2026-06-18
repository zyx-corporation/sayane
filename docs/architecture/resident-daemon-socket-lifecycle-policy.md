# Resident Daemon Socket Lifecycle Policy

Status: Future IPC and mutation policy

Related issues: #210, #211, #215

## Summary

This document defines the policy for future resident daemon socket lifecycle management.

Socket artifacts are communication-surface artifacts. They must not be treated as ordinary stale files.

Current Sayane resident daemon preview commands do not create sockets, delete sockets, bind IPC endpoints, expose resident APIs, or perform readiness checks.

## Core rule

Socket presence is not process identity proof and not API readiness proof.

Socket lifecycle operations must remain separate from diagnostics and generic cleanup.

## Socket evidence layers

A future socket model should separate:

```text
socket artifact exists
-> socket artifact type is valid
-> endpoint is reachable
-> endpoint owner is identified
-> endpoint is authenticated
-> endpoint is authorized
-> protocol is compatible
-> operation class is ready
```

Each layer is stronger than the previous layer.

## Socket artifact vs live endpoint

A socket file or path may exist without a useful live endpoint.

A live endpoint may be reachable but unauthenticated.

An authenticated endpoint may still be unauthorized for a specific operation.

An authorized endpoint may still be protocol-incompatible or not ready for an operation class.

## Socket creation

Future socket creation requires:

```text
explicit operator or daemon launch intent
runtime-root validation
local-only binding policy
authentication policy
authorization policy
audit record
```

Socket creation may expose a communication surface and must not be performed by diagnostic commands.

## Socket replacement

Future socket replacement requires stronger evidence than artifact presence.

Requirements:

```text
explicit operator intent
current endpoint ownership check when possible
process identity evidence when applicable
runtime-root validation
race-safety design
audit record
```

Replacement must fail closed if endpoint ownership is ambiguous.

## Socket deletion

Future socket deletion must not be generic cleanup.

Deletion requires evidence that the socket artifact is stale or unowned and that no active Sayane daemon owns the endpoint.

Requirements:

```text
explicit operator intent
socket-specific evidence
runtime-root validation
owner ambiguity handling
audit record
```

## Local-only requirement

Future resident daemon IPC should be local-first and local-only by default.

Any future network-exposed resident API requires separate policy and must not be introduced through socket diagnostics or readiness checks.

## Authentication and authorization

Future IPC readiness must require authentication and authorization.

Reachability alone is insufficient.

The endpoint must prove that it belongs to the expected runtime root and supports the intended operation class.

## Conservative future statuses

Future socket diagnostics should use conservative statuses such as:

```text
socket_missing
socket_present_type_unverified
socket_type_mismatch
socket_endpoint_unverified
socket_endpoint_unreachable
socket_endpoint_reachable_identity_unverified
socket_endpoint_authenticated
socket_endpoint_unauthorized
socket_protocol_mismatch
socket_operation_not_ready
socket_api_ready
manual_review_required
```

No current command should claim `socket_api_ready`.

## Relationship to cleanup

Socket deletion is not ordinary stale artifact cleanup.

A cleanup apply command must not delete socket artifacts without socket-specific authorization and evidence.

## Relationship to readiness

Socket presence is not API readiness.

Endpoint reachability is not API readiness.

API readiness requires authentication, authorization, compatibility, and operation readiness.

## Audit requirements

Future socket lifecycle operations must record:

- operation type
- runtime root
- socket path
- prior socket diagnostic
- endpoint evidence
- authentication evidence
- authorization evidence
- operator confirmation
- mutation performed
- result
- failure mode
- recovery note

## RDE Delta-M Review

### Preserved

Local IPC remains future work.

Preview commands remain non-mutating.

### Supplemented

The roadmap now treats socket artifacts as communication-surface boundaries.

### Deviation Risks

Do not treat socket files as simple cleanup debris.

Do not treat socket presence as process identity.

Do not treat endpoint reachability as API readiness.

Do not expose IPC or network API behavior through diagnostic commands.
