# Changelog

All notable changes to the Sayane Community Edition (OSS) are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.1] - 2026-05-29

### Added

- Context layering heuristics, profile layout validation, and dogfood documentation updates.
- Expanded Japanese README for beginner onboarding; restored full README_ja sections after edit truncation.

### Changed

- README_ja: Markdown-first storage wording (Obsidian import is optional, not required).
- CONTRIBUTING split into English (`CONTRIBUTING.md`) and Japanese (`CONTRIBUTING_ja.md`); templates reference `README_ja.md`.
- Removed pre-release Omomuki migration notes from user-facing docs (post-1.0 cleanup).
- Recorded Community v1.0.0 release acceptance sign-off in `docs/acceptance-spec.md` (L1/L2 Pass, 2026-05-29).

## [1.0.0] - 2026-05-28

### Changed

- Declared Community Edition `v1.0.0` based on Phase 0-5 scope completion (CLI, Bridge, MCP, Extension, Candidate evaluation, Storage).
- Updated release-facing documentation to use `1.0.0+` acceptance scope and refreshed installation/tag examples to `v1.0.0`.
- Updated package/runtime version metadata from `0.6.0` to `1.0.0`.

## [0.5.9] - 2026-05

- Storage backend plugin contract (`sayane.storage_backends` entry points)
- Default Git auto-commit for profile store changes until encrypted SQLite
- Locale: `SAYANE_LANG` then `LANG` fallback

## [0.5.8] and earlier

See [git history](https://github.com/zyx-corporation/sayane/commits/main) and release tags prior to v0.5.9.

[1.0.1]: https://github.com/zyx-corporation/sayane/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/zyx-corporation/sayane/compare/v0.5.9...v1.0.0
