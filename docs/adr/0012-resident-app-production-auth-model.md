# ADR 0012: Resident App Production Auth Uses Bootstrap Bearer and Dedicated Local UI Session

## Status

Accepted

## Date

2026-06-22

## Context

ADR 0010 chose a Bridge-hosted local resident app shell.

ADR 0011 added cookie-backed local JSON surfaces so that the local shell could fetch screen state
and submit review actions without embedding the Bridge bearer token into page JavaScript.

That local JSON seam was intentionally transitional:

- the first `GET /app/ui` used the Bridge bearer token
- follow-up browser activity reused a local UI cookie
- the cookie convenience seam still effectively depended on the same static bearer credential

For the real app shell, that was no longer enough. The project needed to separate:

- bootstrap or pairing entry
- steady-state browser session continuity
- invalidation and replacement of the browser-facing session

## Decision

The resident app production auth model uses:

1. the existing Bridge bearer token as the bootstrap or pairing credential
2. a dedicated local UI session artifact issued after successful bootstrap entry
3. the dedicated local UI session cookie for follow-up HTML, `/app/ui-state/*`, and
   `/app/ui-action/*` requests

The resident app no longer treats the raw Bridge bearer token as the normal long-lived browser
session credential.

## Consequences

### Positive

- bootstrap credential handling is separated from steady-state UI activity
- browser-side resident app requests no longer depend on re-supplying the raw Bridge bearer
- a new bootstrap entry can replace the prior dedicated UI session cleanly
- dedicated UI session invalidation can happen without rotating the Bridge bearer

### Negative

- the Bridge now maintains one more local auth artifact
- local browser tests must distinguish bootstrap entry from follow-up session behavior

## Boundaries

This decision does not:

- widen candidate or daemon mutation scope
- change app-facing resident endpoint paths or payload contracts
- introduce OS keychain, OAuth, or remote account integration
- redesign authorization policy beyond the local resident app shell

## Related

- `docs/adr/0010-resident-app-first-real-ui-container.md`
- `docs/adr/0011-resident-app-local-ui-session-json-surfaces.md`
- `docs/release/v1.0.14-production-auth-model-design-note.md`
