# Resident Daemon Cleanup Decision Model

This document records #200 resident daemon cleanup decision model.

## Status

Read-only decision preview.

No cleanup, deletion, repair, directory creation, lock acquisition, socket creation, or process control is implemented.

## Purpose

#199 added stale artifact diagnostics.

#200 adds a conservative decision layer on top of those diagnostics.

The model answers:

```text
Given what we can observe, what should a future cleanup implementation do?
```

It does not perform the action.

## Command

```bash
sayane app daemon-cleanup-decisions --json
```

Optional runtime root override:

```bash
sayane app daemon-cleanup-decisions --runtime-root /path/to/runtime --json
```

## Recommendations

The decision model can emit:

```text
no_action
manual_review_required
unsafe_to_delete
future_cleanup_candidate
```

Current behavior is intentionally conservative.

## Current decision rules

### Missing artifact

```text
missing -> no_action
```

A missing artifact does not require cleanup.

### Present artifact

```text
present_review_required -> manual_review_required
```

A present artifact requires review because preview diagnostics do not prove ownership, liveness, or safety.

### Type mismatch

```text
type_mismatch_review_required -> unsafe_to_delete
```

An unexpected type at a daemon-owned path is not considered safe to delete.

It requires manual review.

## Payload

Top-level payload fields include:

```text
kind
preview_only
runtime_root
decision_policy
deletes_artifacts
repairs_artifacts
mutates_filesystem
manual_review_required
decisions
```

Each decision includes:

```text
artifact_kind
path
diagnostic_status
recommendation
reason
manual_review_required
safe_to_delete
deletes_artifact
repairs_artifact
mutates_filesystem
```

## Safety guarantees

The cleanup decision model does not:

- delete artifacts
- repair artifacts
- create runtime directories
- write PID files
- acquire locks
- create sockets
- write logs
- write temp files
- write state files
- control processes

It explicitly reports:

```text
deletes_artifacts: false
repairs_artifacts: false
mutates_filesystem: false
preview_only: true
```

No current decision marks an artifact as safe to delete.

```text
safe_to_delete: false
```

## Relationship to previous resident daemon work

```text
#198 filesystem mutation policy
#199 stale artifact diagnostic preview
#200 cleanup decision preview
```

The model separates observation, decision, and mutation.

Only observation and decision exist today.

Mutation remains out of scope.

## Future extension

A future cleanup implementation may add stronger checks before allowing cleanup candidates, such as:

- process liveness verification
- process identity verification
- user ownership verification
- runtime root ownership verification
- lock ownership verification
- socket liveness verification

Only after those checks exist may a future decision become:

```text
future_cleanup_candidate
```

Even then, a separate mutating command must be introduced explicitly.

## RDE Delta-M Review

### Preserved

Preview commands remain non-mutating.

Diagnostics remain conservative.

Manual review remains the default for ambiguity.

### Supplemented

The system now separates stale artifact observation from cleanup decision-making.

Future cleanup implementation has a stable non-mutating decision seam.

### Deviation Risks

Do not infer that `manual_review_required` means stale or safe to delete.

Do not infer that `unsafe_to_delete` means malicious.

Do not add filesystem mutation to this decision model.

Do not reuse this preview command name for a mutating cleanup command.
