# Changelog

All notable changes to the Sayane Community Edition (OSS) are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Phase 6–17 release closure: context acceptance, semantic review, human review workflow, audit trail, bundle provenance, regression dashboard, policy profiles, custom policy files, cryptographic signing, and signed export packages. See docs/release/phase6-17-release-closure.md.
- Add public narrative and architecture documentation for Sayane context acceptance and verifiable handoff.
- Add CLI command reference for review, audit, policy, signing, and package workflows.

## [1.0.3] - 2026-05-31

### Added

- **Local Open WebUI compile adapter** — `sayane compile --target local-openwebui` (OpenAI-compatible messages for localhost Open WebUI).
- **PyPI package `sayane`** — first publish to PyPI ([#82](https://github.com/zyx-corporation/sayane/issues/82)).

### Changed

- Extension: Open WebUI insert moved from preview to active buttons (Bridge compile supported; Extension **0.3.6**).
- Extension **0.3.7**: Open WebUI URL matching for `/c/{id}` routes and dynamic `#chat-input-*` selectors.
- Extension **0.3.8**: Relax localhost Open WebUI path matching (SPA routes); support `[::1]`; clearer SITE_MISMATCH hint.
- `docs/install.md`: PyPI install instructions (`pip install sayane`).

## [1.0.2] - 2026-05-30

### Added

- **DeepSeek compile adapter** — OpenAI-compatible chat messages for `sayane compile --target deepseek`.
- **Gemini compile adapter** (`GeminiAdapter`) — `sayane compile --target gemini` and Bridge `/context-packet?target=gemini` ([#85](https://github.com/zyx-corporation/sayane/issues/85)).
- **CLI `sayane capture`** — save pending Candidate from `--text`, `--file`, or stdin ([#84](https://github.com/zyx-corporation/sayane/issues/84)).
- Extension provider registry with dynamic popup insert UI ([#96](https://github.com/zyx-corporation/sayane/issues/96)).
- Draft WinGet / Scoop packaging manifests under `packaging/` ([#83](https://github.com/zyx-corporation/sayane/issues/83)).
- L3 Playwright E2E pass record in `docs/acceptance-spec.md` §6.1.

### Changed

- Extension **0.3.5**: active insert for ChatGPT, Claude, Gemini, DeepSeek; local providers remain in collapsed preview.
- Extension E2E global-setup runs `npm run build`; selectors use `[data-provider-id]`.
- `docs/install.md`: WinGet / Scoop preview section.
- `docs/acceptance-spec.md` §9: sayane-pro hooks RecursionError fixed (`eae09d8`).

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

[Unreleased]: https://github.com/zyx-corporation/sayane/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/zyx-corporation/sayane/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/zyx-corporation/sayane/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/zyx-corporation/sayane/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/zyx-corporation/sayane/compare/v0.5.9...v1.0.0
