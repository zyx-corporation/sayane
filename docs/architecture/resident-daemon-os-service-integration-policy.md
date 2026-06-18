# Resident Daemon OS Service Integration Policy

Status: Future platform integration policy

Related issues: #218, #219, #220

## Summary

This document defines the policy for future resident daemon OS service integration.

OS service integration includes systemd units, launchd agents, Windows services, auto-start behavior, service installation, service enablement, service disablement, service removal, and service repair.

Current Sayane resident daemon preview commands do not integrate with OS service managers.

## Core rule

OS service integration is platform-specific high-risk future work.

It must not be introduced as a side effect of runtime initialization, process control, cleanup, repair, or IPC setup.

## Current boundary

Current commands do not:

- install service files
- enable auto-start
- disable services
- remove services
- repair service definitions
- call platform service managers
- request elevated privileges
- supervise daemon processes through OS service managers

## Supported platform policy

Future service integration must document behavior separately for each supported platform:

- Linux systemd user service
- Linux systemd system service
- macOS launchd user agent
- macOS launchd daemon
- Windows service

Unsupported platforms must fail closed with clear messaging.

## Privilege boundary

Future service integration must state whether the operation is user-level or system-level.

System-level operations require stronger operator confirmation and rollback instructions.

A future command must not silently escalate privileges.

## Install requirements

Future service installation requires:

- explicit operator intent
- platform-specific template review
- runtime root validation
- executable path validation
- environment validation
- privilege boundary disclosure
- rollback/uninstall plan
- audit record

## Enable and disable requirements

Future service enablement or disablement requires:

- explicit operator intent
- platform-specific command disclosure
- current service state check
- expected post-state
- rollback note
- audit record

Enablement must not automatically start a daemon unless explicitly requested and accepted.

## Repair requirements

Future service repair is distinct from service installation.

Repair must include:

- prior service definition capture where possible
- proposed replacement definition
- diff or summary
- explicit confirmation
- rollback path
- audit record

## Uninstall requirements

Future service removal requires:

- explicit operator intent
- current service state check
- stop policy if service is active
- removal plan
- residual artifact report
- audit record

Uninstall must not delete user data or runtime artifacts unless a separate cleanup policy authorizes it.

## Relationship to process control

OS service integration is not ordinary process control.

A service manager may restart processes, persist state, and affect login or boot behavior.

Therefore service integration requires platform-specific policy beyond daemon start/stop commands.

## Relationship to runtime initialization

Runtime initialization must not install or enable services.

Runtime initialization may prepare local directories, but service integration controls persistence and auto-start behavior.

## Audit requirements

Future service integration commands must record:

- platform
- service class
- user-level or system-level scope
- service name
- command attempted
- service definition path
- prior service state
- desired service state
- privilege boundary
- operator confirmation
- result
- rollback note

## RDE Delta-M Review

### Preserved

No OS service integration exists in the current preview track.

Operator consent remains required for future high-risk operations.

### Supplemented

The roadmap now defines the platform service-management gate.

### Deviation Risks

Do not introduce auto-start as a side effect of runtime initialization.

Do not silently escalate privileges.

Do not combine service repair with artifact cleanup or runtime repair.
