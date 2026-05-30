# WinGet manifest (draft)

Community Edition WinGet packaging scaffold for **Issue #83**.

## Status

- **Not published** to [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs).
- Manifest template: `zyx-corporation.sayane.yaml` (commented YAML — uncomment and fill `InstallerSha256` on release).

## Install model

Sayane Community on Windows is installed via `scripts/install.ps1` (user venv under `%LOCALAPPDATA%\Sayane`). WinGet submission options:

1. **Zip + nested script** (template): download release tag archive, run `install.ps1`.
2. **Portable wrapper** (future): ship a small `sayane.cmd` launcher in a release asset.

PyPI (#82) or a signed MSI (sayane-pro) may supersede this path later.

## Submission checklist

1. Tag release `vX.Y.Z` on `zyx-corporation/sayane`.
2. Update `PackageVersion` and `InstallerUrl` in the manifest.
3. Run `winget validate packaging/winget/zyx-corporation.sayane.yaml` (after uncommenting).
4. Open PR to `microsoft/winget-pkgs` under `manifests/z/yx-corporation.sayane/<version>/`.

## Local validation

```powershell
# After uncommenting the manifest and setting SHA256:
winget validate .\packaging\winget\zyx-corporation.sayane.yaml
```

## User install (today)

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

See [docs/install.md](../../docs/install.md).
