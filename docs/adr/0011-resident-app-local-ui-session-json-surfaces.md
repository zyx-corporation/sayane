# ADR 0011: Resident App Local UI Session JSON Surfaces

Status: Accepted

## Context

ADR 0010 chose a Bridge-hosted Sayane Resident App local shell as the first real resident app UI container.

That decision exposed a practical integration gap:

- the existing app-facing JSON surfaces (`/app/...`) were bearer-token oriented
- the local browser shell at `/app/ui` could continue navigation with a local UI session cookie
- a real local shell still needed same-origin JSON reads and writes for queue, detail, diff, lineage,
  daemon, and candidate actions

Without an explicit local JSON seam, the project would either:

1. duplicate resident app logic in server-rendered HTML/forms only
2. push the browser shell back toward bearer-token handling in page JavaScript
3. introduce a separate mutation model only for the local shell

All three options would increase drift or weaken the current auth and review boundaries.

## Decision

The Bridge-hosted local resident app shell uses dedicated cookie-backed JSON surfaces:

```text
GET  /app/ui-state/contract
GET  /app/ui-state/home
GET  /app/ui-state/candidates
GET  /app/ui-state/candidates/{id}
GET  /app/ui-state/candidates/{id}/diff
GET  /app/ui-state/candidates/{id}/lineage
GET  /app/ui-state/daemon

POST /app/ui-action/capture-clipboard
POST /app/ui-action/candidates/{id}/evaluate
POST /app/ui-action/candidates/{id}/approve
POST /app/ui-action/candidates/{id}/reject
POST /app/ui-action/candidates/{id}/revise
```

These surfaces:

- are protected by the existing local UI session cookie established from `/app/ui`
- reuse the same app-layer builders and candidate-review behavior as the bearer-token `/app/...`
  surfaces
- remain local-shell integration seams, not a new product-wide auth model

## Consequences

### Positive

- The first real local shell can use same-origin `fetch` without embedding the bearer token into page
  JavaScript.
- HTML fallback pages and the JSON shell remain aligned on the same resident app semantics.
- Candidate and daemon behavior stays inside the existing review / preview boundaries.
- The extension compatibility surface can keep using bearer-backed background fetches without being
  forced into the local cookie model.

### Negative

- The Bridge now exposes two integration families for similar resident app semantics:
  bearer-token `/app/...` and cookie-backed `/app/ui-state/...` / `/app/ui-action/...`.
- Documentation and contract metadata must make the difference explicit to avoid confusion.

## Boundaries

This ADR does not choose the final production auth model.

It does not:

- make the UI session cookie a network-exposed multi-client auth strategy
- introduce direct profile patch endpoints
- widen daemon previews into daemon identity or API readiness proof
- replace the extension compatibility surface as the only other UI integration path

## Related

- `docs/adr/0010-resident-app-first-real-ui-container.md`
- `docs/architecture/resident-app-bootstrap-ui.md`
- `docs/architecture/resident-app-ui-integration-contract.md`
