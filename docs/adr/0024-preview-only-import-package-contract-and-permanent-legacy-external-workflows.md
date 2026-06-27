# ADR 0024: Preview-only `import-package` contract and permanent legacy external workflows

## Status

Accepted — 2026-06-28

## Context

After ADR 0022 and ADR 0023, two remaining ambiguities still existed:

1. whether `sayane storage import-package` should silently evolve into a
   mutating import path
2. whether older Obsidian / Git external workflows were only temporarily
   legacy, or permanently outside the supported primary path

Those ambiguities make it too easy for operators to misread preview output as a
soft staging import, or to assume that external vault / Git workflows will
eventually return as canonical working-store paths.

## Decision

### 1. `import-package` remains preview-only by contract

The package manifest boundary declares:

- `import_contract = preview_only`
- `profile_mutation_allowed = false`
- `candidate_persistence_allowed = false`
- `reserved_future_mutating_workflow = separate_explicit_review_queue_import`

Any future mutating package intake must use a **separate explicit workflow**.
It must not be introduced by changing the meaning of `import-package`.

That separate explicit workflow is now:

- `docs/adr/0026-explicit-review-queue-import-command-for-vault-aware-packages.md`

### 2. Permanent legacy external workflows

The following workflows remain permanent legacy compatibility paths rather than
future primary paths:

- Obsidian markdown import via `sayane storage import --legacy-compatible`
- Obsidian markdown export via `sayane storage export --legacy-compatible`
- Git commit of the filesystem profile store via `sayane storage commit --legacy-compatible`

These may remain available for manual operator compatibility, but they are not
the path by which high-sensitivity working state returns to canonical storage.

## Consequences

Positive:

- CLI behavior stays fail-closed
- preview surfaces keep a stable meaning
- legacy compatibility remains available without blurring the supported path

Negative:

- users wanting persisted review queues from packages need a distinct future
  command
- older manual workflows remain explicitly second-class

## Related

- `docs/adr/0022-vault-aware-external-packages-are-the-supported-reviewable-exchange-format.md`
- `docs/adr/0023-supported-and-forbidden-external-workflows-for-vault-aware-packages.md`
- `docs/storage-manual.md`
