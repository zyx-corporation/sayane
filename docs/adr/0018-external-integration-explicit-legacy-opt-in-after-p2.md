# ADR 0018: External Integrations Become Explicit Legacy Opt-In After P2

## Status

Accepted

## Date

2026-06-28

## Context

P2 closed the migration of `Candidate`, `ReviewDecision`, and `Lineage` onto
vault-aware repositories when an explicit Local Vault runtime is active.

At the same time, the repository still carries historical Community workflows
for:

- Obsidian import
- Obsidian export
- Git commit of the profile store

Those workflows are useful for compatibility and manual operator workflows, but
they remain outside the main Local Vault security path. Leaving them as casual
or implicit defaults would blur the post-P2 storage boundary again.

The project therefore needs a first P3 rule that narrows external integrations
before any richer redesign is attempted.

## Decision

After P2, Obsidian import/export and Git commit remain available only as
**explicit legacy compatibility paths**.

The first P3 enforcement slice is:

1. `sayane storage import` requires explicit confirmation for mutating use
2. `sayane storage export` requires explicit confirmation
3. `sayane storage commit` requires explicit confirmation
4. `sayane init` no longer creates a Git repository or commit implicitly
5. dry-run inspection may remain available without the same confirmation because
   it does not mutate the local profile store or external target

The explicit confirmation flag is:

`--legacy-compatible`

This flag does not mean the path is preferred. It means the operator is
knowingly choosing a compatibility workflow that sits outside the main Local
Vault-sensitive-state path.

## Consequences

### Positive

- storage docs and CLI behavior now match the post-P2 security posture better
- accidental re-promotion of Obsidian/Git workflows into default operator paths
  becomes harder
- the repo can keep compatibility workflows without pretending they are the
  primary product direction

### Negative

- existing manual workflows become slightly noisier
- some historical acceptance/docs examples need migration to the explicit flag

## Boundaries

This decision does not:

- remove Obsidian import/export or Git commit
- redesign bidirectional sync semantics
- define a vault-aware external export format
- make external integration production-complete

## Related

- `docs/adr/0017-transitional-filesystem-working-store-boundary-after-p2.md`
- `docs/roadmap.md`
- `docs/storage-manual.md`
