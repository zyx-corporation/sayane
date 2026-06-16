# Resident Capability Policy

This document records #186 capability issuer production hardening follow-up.

## Status

Initial policy seams are implemented.

This is not final production authentication.

## Policy Object

`CapabilityIssuerPolicy` records non-secret assumptions for local capability issuance:

```text
name
token_persistence
unlock_session_binding
network_auth
cryptographic_signing
production_ready
```

The default policy is local development only:

```text
token_persistence: non_persistent
unlock_session_binding: unbound
network_auth: not_supported
cryptographic_signing: not_supported
production_ready: false
```

## Surface Issuers

Dedicated local issuers can be created per resident surface:

```text
capture
ui
mcp
bridge
admin
```

Each issued token records its surface.

`admin` remains an explicit all-capability override.

## Persistence Policy

Persistent resident tokens are intentionally rejected for now.

The boundary is explicit so a later implementation can add OS keychain or durable session support without silently changing local development semantics.

## Unlock Session Policy

Unlock-session binding is recorded as `unbound` by default.

This means capability tokens do not yet prove that a vault has been unlocked or that a durable resident session exists.

## Non-goals

This work does not add:

- OS keychain integration
- OAuth
- network authentication
- durable token storage
- cryptographic token signing
- resident daemon lifecycle

## RDE Delta-M Review

### Preserved

The local token model remains simple and testable.

Production authentication is not invented prematurely.

### Supplemented

Token persistence and unlock-session assumptions are now inspectable.

Surface-specific issuance makes capture, UI, MCP, Bridge, and admin easier to audit.

### Deviation Risk

Do not treat this local policy as production auth.

Do not persist resident tokens until the OS/session model is reviewed.
