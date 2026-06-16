# Changelog

All notable changes to the Sayane Community Edition (OSS) are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.0.6] - 2026-06-17 Resident Foundation

### Summary

Sayane v1.0.6 closes the front-loaded resident app and Local Vault foundation work for ADR 0007. It establishes shared repository boundaries, SQLite-backed Local Vault MVP persistence, resident runtime selection, read-only resident preview CLI surfaces, and local capability policy seams without introducing a production daemon or production authentication.

### Added

- Repository contracts and test providers for Candidate, ReviewDecision, Lineage, profile context, project context, and RepositoryBundle.
- ReviewDecision repository seam for `save_decision()`, `list_decisions()`, `load_review_decisions()`, and `get_decisions_for_candidate()`.
- SQLite-backed Local Vault MVP path for Candidate, ReviewDecision, and Lineage persistence tests.
- Resident app service boundary and runtime builder.
- Clipboard capture through `sayane app capture-clipboard` as pending Candidate input.
- `sayane app serve` delegation plan to the existing Bridge server path.
- Resident review queue and MCP preview skeletons.
- Read-only CLI preview commands:
  - `sayane app review-queue --json`
  - `sayane app mcp-preview --json`
- Resident runtime repository backend selection policy:
  - `legacy_process_local`
  - `injected_repository_bundle`
  - `sqlite_test_local_vault`
  - `future_pro_backend`
- Capability issuer metadata, expiry checks, surface-scoped local token issuance, and local capability policy metadata.
- Architecture docs for repository boundary, SQLite MVP, resident runtime selection, resident review queue CLI, and resident capability policy.

### Changed

- Resident runtime diagnostics now expose non-sensitive repository backend and storage boundary metadata.
- Runtime-issued capabilities are separated for capture, UI, MCP, and admin surfaces.
- Default resident runtime remains compatibility-first and does not silently promote test storage into production state.

### Security

- Capability issuer policy now makes token persistence, unlock-session binding, network auth, signing, and production-readiness assumptions explicit.
- Persistent resident capability tokens remain unsupported by default.
- `sqlite_test_local_vault` remains explicitly test-only and requires opt-in.

### Non-goals retained

- No production resident daemon lifecycle.
- No OS keychain integration.
- No durable token persistence.
- No network authentication.
- No pro backend implementation.

## [1.0.0] - 2026-06-05 Context Acceptance

### Summary

Sayane v1.0.0 is the first stable architecture release for local-first LLM context acceptance, completing the Phase 3-19 implementation chain.

### Added

- Candidate-based context import flow
- Semantic Review for overlap, unstable placement, boundary-sensitive
- Human review workflow: approve, reject, modify, defer
- Append-only audit trail
- Bundle provenance and SHA-256 verification
- Transfer regression dashboard
- Policy profiles and custom policy files
- Decision diff viewer
- Audit export in Markdown/JSON/JSONL
- Ed25519 signing and tamper detection
- Signed export package
- Public narrative, architecture diagrams, CLI reference


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

[Unreleased]: https://github.com/zyx-corporation/sayane/compare/v1.0.6...HEAD
[1.0.6]: https://github.com/zyx-corporation/sayane/compare/v1.0.3...v1.0.6
[1.0.3]: https://github.com/zyx-corporation/sayane/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/zyx-corporation/sayane/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/zyx-corporation/sayane/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/zyx-corporation/sayane/compare/v0.5.9...v1.0.0
