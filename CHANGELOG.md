# Changelog

All notable changes to the Sayane Community Edition (OSS) are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.6.0] - 2026-05-24

### Changed

- **Project rename**: Omomuki → **Sayane（紗綾音）**
- Python package `omomuki` → `sayane`; CLI command `sayane`
- Default profile store `~/.omomuki/` → `~/.sayane/`
- Profile file `omomuki.profile.yaml` → `sayane.profile.yaml`
- Schema kind `OmomukiProfile` → `SayaneProfile`
- Environment variables `OMOMUKI_*` → `SAYANE_*`
- GitHub repository: `zyx-corporation/sayane` (formerly `omomuki`)
- Commercial Edition package name: licensed separately (formerly `omomuki-pro`)

### Added

- [Migration guide](docs/migration-omomuki-to-sayane.md) for existing Omomuki users
- README titles include kanji name: Sayane (紗綾音)

### Notes

- PyPI distribution under the name `sayane` is not yet published; use install scripts or `pip install` from Git tags.
- See migration guide before upgrading an existing `~/.omomuki/` profile store.

## [0.5.9] - 2026-05

- Storage backend plugin contract (`sayane.storage_backends` entry points)
- Default Git auto-commit for profile store changes until encrypted SQLite
- Locale: `SAYANE_LANG` then `LANG` fallback

## [0.5.8] and earlier

See [git history](https://github.com/zyx-corporation/sayane/commits/main) and release tags prior to the rename.

[0.6.0]: https://github.com/zyx-corporation/sayane/compare/v0.5.9...v0.6.0
