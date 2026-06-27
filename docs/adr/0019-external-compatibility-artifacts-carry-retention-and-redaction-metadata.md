# ADR 0019: External Compatibility Artifacts Carry Retention and Redaction Metadata

## Status

Accepted

## Date

2026-06-28

## Context

P3 already narrowed Obsidian import/export and Git commit into explicit legacy
compatibility workflows.

That still leaves one practical ambiguity: once Sayane writes a compatibility
artifact into an external vault or folder, the artifact can be mistaken for a
long-lived or canonical export unless the boundary is carried with the artifact
itself.

The first executable answer does not need a full supported sync model yet. It
does need the export artifact to carry:

1. redaction posture
2. retention guidance
3. non-canonical / review-required status

## Decision

Legacy external compatibility exports must carry machine-readable metadata and a
human-readable notice that state:

1. the artifact is derived context, not canonical profile state
2. local source paths are redacted
3. raw capture, review history, and lineage history are not included
4. the artifact should be deleted after import or review unless a separate
   retention decision exists
5. canonical promotion still requires Candidate Review

The current Community contract uses:

- `sayane-export-metadata.json`
- `SAYANE_EXPORT_NOTICE.txt`

## Consequences

### Positive

- exported artifacts now carry the same boundary even when separated from the
  original CLI invocation
- local absolute paths do not leak into compatibility-export metadata
- P3 retention/redaction work becomes partially executable instead of purely
  narrative

### Negative

- this is still guidance metadata, not full lifecycle enforcement
- future supported export formats may replace or supersede this compatibility
  contract

## Boundaries

This decision does not:

- define a final supported external sync protocol
- define automated deletion enforcement
- define per-class retention overrides
- convert compatibility exports into a supported canonical interchange format

## Related

- `docs/adr/0018-external-integration-explicit-legacy-opt-in-after-p2.md`
- `docs/storage-manual.md`
