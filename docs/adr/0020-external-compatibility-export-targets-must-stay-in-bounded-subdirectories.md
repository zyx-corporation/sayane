# ADR 0020: External Compatibility Export Targets Must Stay in Bounded Subdirectories

## Status

Accepted

## Date

2026-06-28

## Context

P3 already made mutating external integrations explicit legacy compatibility
workflows and added retention/redaction metadata to exported artifacts.

One remaining ambiguity is the target path itself. If compatibility export can
write into vault root, hidden metadata directories, or path-escaping targets,
the project risks reintroducing accidental spread into locations that look more
authoritative than they are.

## Decision

Compatibility export targets must stay inside an explicit bounded subdirectory
under the chosen external vault root.

The current executable rules are:

1. export subdir must be relative
2. export subdir must not be empty
3. export subdir must not contain `.`, `..`, or path-escape segments
4. export subdir must not target hidden or reserved directories such as
   `.obsidian`, `.git`, `node_modules`, or dot-prefixed names

## Consequences

### Positive

- compatibility exports remain visibly separate from ordinary vault root content
- dangerous hidden/reserved paths are blocked before write
- supported path versus forbidden path becomes executable, not just documented

### Negative

- some historical export habits may need a different explicit subdirectory

## Boundaries

This decision does not:

- define final supported bidirectional sync
- define a canonical external package format
- guarantee downstream tools will preserve the same boundary after export

## Related

- `docs/adr/0018-external-integration-explicit-legacy-opt-in-after-p2.md`
- `docs/adr/0019-external-compatibility-artifacts-carry-retention-and-redaction-metadata.md`
- `docs/storage-manual.md`
