# Scoop bucket manifest (draft)

Community Edition Scoop packaging scaffold for **Issue #83**.

## Status

- **Not published** to a public Scoop bucket yet.
- Manifest template: `sayane.json`

## Prerequisites

Users need **Python 3.11+** and **git** (same as [install.ps1](../../scripts/install.ps1)).

## Add to a custom bucket

```powershell
scoop bucket add sayane https://github.com/zyx-corporation/sayane
# Or copy packaging/scoop/sayane.json into your bucket as sayane.json
scoop install sayane
```

For a monorepo bucket, point `scoop bucket add` at a repo that contains only `bucket/sayane.json` — this folder is a **template** inside the main sayane repo.

## Version bumps

1. Update `"version"` in `sayane.json`.
2. `autoupdate.url` uses `v$version` — tag must exist on GitHub.
3. Run `scoop checkver sayane` if integrated into a bucket with checkver support.

## User install (today)

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

See [docs/install.md](../../docs/install.md).
