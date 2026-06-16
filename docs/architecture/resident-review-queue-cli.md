# Resident Review Queue CLI

This document records #185 resident review queue CLI previews.

## Status

Initial read-only CLI previews are implemented.

This is not a final GUI, daemon endpoint, or mutation API.

## Commands

```bash
sayane app review-queue --json
sayane app mcp-preview --json
```

## Boundary

The commands follow this dependency direction:

```text
CLI
  -> build_resident_runtime()
  -> ResidentAppService / RepositoryBundle
  -> build_review_queue() / build_mcp_preview()
```

The CLI must not import SQLite runtime, Vault adapters, or future backend builders directly.

## Review Queue

`review-queue` returns a `resident_review_queue` payload.

It is a review surface and not MCP context.

When no repository bundle is selected, it returns an empty stable payload with:

```text
repository_available: false
```

When repositories are available, it calls:

```text
build_review_queue(..., capability=ui)
```

## MCP Preview

`mcp-preview` returns a derived preview payload.

It is not canonical profile state.

When no repository bundle is selected, it returns an empty stable payload with:

```text
repository_available: false
```

When repositories are available, it calls:

```text
build_mcp_preview(..., capability=mcp)
```

## Non-goals

This work does not add:

- approve/reject commands
- profile context writes
- final GUI screens
- network server endpoints
- daemon lifecycle changes

## RDE Delta-M Review

### Preserved

Candidate review remains a human review surface.

MCP preview remains derived context.

Runtime selection remains the state boundary.

### Supplemented

Operators and future UI code now have stable JSON preview payloads.

### Deviation Risk

Do not treat `mcp-preview` as canonical profile state.

Do not add mutation shortcuts through this preview path.
