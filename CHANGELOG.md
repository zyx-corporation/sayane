# Changelog

All notable changes to the Sayane Community Edition (OSS) are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Planned for v1.0.13 Resident Daemon Preflight Schema Preview

- Schema-only resident daemon event record support for future preview/apply/process/IPC/service audit shapes.
- Resident daemon implementation gate preflight checklist:
  - `sayane app daemon-preflight --json`
  - `sayane app daemon-preflight --json --include-event-record`
- Schema-only helper for deriving a preview event record from a preflight report.
- Schema-only resident daemon state machine covering future states and transition edges.
- Additional architecture docs for:
  - resident daemon event record schema
  - resident daemon preflight checklist
  - resident daemon state machine schema

### Safety boundary retained

- No production resident daemon runtime.
- No daemon process start, stop, restart, signal sending, or supervision.
- No process probing.
- No PID file writes.
- No lock acquisition, release, or stealing.
- No socket creation.
- No IPC endpoint exposure.
- No runtime directory creation.
- No stale artifact deletion.
- No artifact repair.
- No OS service integration.
- No persistent IPC credentials.
- No network-exposed resident API.

## [1.0.12] - 2026-06-18 Resident Daemon Policy Gate

### Summary

Sayane v1.0.12 packages the Resident Daemon Policy Gate work. It adds the architecture and governance policies required before actual resident daemon implementation may begin, while preserving the existing preview-only, non-mutating safety boundary.

### Added

- Resident daemon roadmap snapshot for the v1.0.12 policy gate:
  - `docs/architecture/resident-daemon-roadmap-snapshot-v1.0.12.md`
- Release notes for v1.0.12 Resident Daemon Policy Gate.
- Liveness diagnostic preview command:
  - `sayane app daemon-liveness-diagnostic --json`
- Optional liveness diagnostic runtime root override:
  - `sayane app daemon-liveness-diagnostic --runtime-root /path/to/runtime --json`
- Architecture policy documents for:
  - process liveness proof
  - liveness diagnostics
  - process existence verification
  - process identity verification
  - readiness and API readiness
  - mutation authorization
  - cleanup apply commands
  - artifact repair
  - lock ownership
  - socket lifecycle
  - runtime initialization
  - local IPC authentication
  - operator runbook and consent
  - process control
  - OS service integration
  - implementation readiness gate

### Policy gate

The resident daemon evidence ladder is now documented as:

```text
PID parse validity
-> process existence
-> process identity
-> daemon readiness
-> API readiness
```

The mutation and operation ladder is now documented as:

```text
diagnostic evidence
-> decision preview
-> operator authorization
-> mutation or control command
-> audit record
```

Actual resident daemon implementation remains future work until a future implementation issue explicitly accepts the readiness gate.

### CI

The following operator-reported GitHub Actions runs completed successfully during this workstream:

- #163 `docs(app): add resident daemon liveness diagnostic preview`
- #641 `docs(app): add resident daemon readiness policy`
- #643 `docs(app): add resident daemon cleanup apply policy`
- #171 `docs(app): add resident daemon socket lifecycle policy`
- #174 `docs(app): add resident daemon operator consent policy`
- #177 `docs(app): add resident daemon implementation readiness gate`

CI for the v1.0.12 release-prep commit must be recorded separately before closing the release-prep issue.

### Non-goals retained

- No production resident daemon runtime.
- No daemon process start, stop, restart, signal sending, or supervision.
- No process probing.
- No PID file writes.
- No lock acquisition, release, or stealing.
- No socket creation.
- No IPC endpoint exposure.
- No runtime directory creation.
- No stale artifact deletion.
- No artifact repair.
- No OS service integration.
- No persistent IPC credentials.
- No network-exposed resident API.

## [1.0.11] - 2026-06-17 Resident Daemon PID File Diagnostic Preview

### Summary

Sayane v1.0.11 packages the resident daemon PID file diagnostic preview track. It adds a read-only PID file parse diagnostic for the planned resident daemon PID artifact without proving daemon liveness, probing processes, controlling processes, or mutating filesystem state.

### Added

- Read-only PID file diagnostic model for the planned resident daemon PID artifact.
- PID file diagnostic CLI command:
  - `sayane app daemon-pid-diagnostic --json`
- Optional PID file diagnostic runtime root override:
  - `sayane app daemon-pid-diagnostic --runtime-root /path/to/runtime --json`
- Architecture docs for PID file diagnostics.
- Release notes for v1.0.11 Resident Daemon PID File Diagnostic Preview.

### PID parse statuses

- `missing`
- `unreadable`
- `empty`
- `invalid`
- `parsed`

`parsed` means only that PID file content was parsed as a positive integer string. It is not daemon liveness proof and does not prove that a process is Sayane.

### Security

- PID file diagnostics do not create, delete, repair, or rewrite PID files.
- PID file diagnostics do not probe process liveness.
- PID file diagnostics do not send signals.
- PID file diagnostics do not control processes.
- PID file diagnostics do not acquire locks.
- PID file diagnostics do not create sockets or runtime directories.
- The diagnostic payload keeps `proves_liveness`, `probes_process`, `controls_process`, and `mutates_filesystem` false.

### CI

- GitHub Actions run #627 completed successfully on `main` after the PID file diagnostic preview work.

### Non-goals retained

- No production resident daemon process control.
- No OS service integration.
- No PID file writes.
- No lock acquisition.
- No socket creation.
- No process liveness probing.
- No stale artifact deletion or repair.

## [1.0.10] - 2026-06-17 Resident Daemon Cleanup Decision Preview

### Summary

Sayane v1.0.10 packages the resident daemon cleanup decision preview track. It adds read-only stale artifact diagnostics and a non-mutating cleanup decision model for planned resident daemon runtime artifacts.

### Added

- Read-only stale artifact diagnostic model for planned resident daemon artifacts.
- Stale artifact diagnostic CLI command:
  - `sayane app daemon-stale-artifacts --json`
- Optional stale artifact diagnostic runtime root override:
  - `sayane app daemon-stale-artifacts --runtime-root /path/to/runtime --json`
- Non-mutating cleanup decision model.
- Cleanup decision CLI command:
  - `sayane app daemon-cleanup-decisions --json`
- Optional cleanup decision runtime root override:
  - `sayane app daemon-cleanup-decisions --runtime-root /path/to/runtime --json`
- Architecture docs for stale artifact diagnostics and cleanup decision model.

### Cleanup decision rules

- `missing -> no_action`
- `present_review_required -> manual_review_required`
- `type_mismatch_review_required -> unsafe_to_delete`

### Security

- Stale artifact diagnostics do not delete or repair artifacts.
- Cleanup decisions do not delete or repair artifacts.
- No command creates runtime directories.
- No command writes PID, lock, socket, log, temp, or state files.
- No command acquires locks.
- No command controls processes.
- No current cleanup decision marks an artifact as safe to delete without stronger future checks.

### CI

- GitHub Actions run #138 completed successfully on `main` after the cleanup decision preview work.

### Non-goals retained

- No production resident daemon process control.
- No OS service integration.
- No PID file writes.
- No lock acquisition.
- No socket creation.
- No stale artifact deletion or repair.

## [1.0.9] - 2026-06-17 Resident Daemon Runtime Layout Preview

### Summary

Sayane v1.0.9 packages the resident daemon runtime layout preview track. It adds a plan-only runtime directory layout contract, exposes the layout through a read-only CLI preview, and fixes CLI version reporting so it follows installed package metadata.

### Added

- Resident daemon runtime directory layout contract.
- Planned runtime directories:
  - `pid`
  - `lock`
  - `socket`
  - `log`
  - `tmp`
  - `state`
- Runtime-root path validation for layout child paths.
- Read-only daemon runtime layout CLI command:
  - `sayane app daemon-runtime-layout --json`
- Optional runtime root override:
  - `sayane app daemon-runtime-layout --runtime-root /path/to/runtime --json`
- Architecture docs for runtime layout contract and runtime layout CLI preview.

### Changed

- `sayane --version` now reads installed package metadata instead of stale source constants.
- Package tests now assert version metadata consistency.

### Security

- Runtime layout preview does not create directories.
- Runtime layout preview does not write PID, lock, socket, log, temp, or state files.
- Runtime layout preview does not acquire locks.
- Runtime layout preview does not control processes.
- Path escape attempts are rejected by the app-layer runtime layout model.

### CI

- GitHub Actions run #116 completed successfully on `main` after the runtime layout CLI preview work.

### Non-goals retained

- No production resident daemon process control.
- No OS service integration.
- No PID file writes.
- No lock acquisition.
- No socket creation.
- No stale runtime file cleanup.

## [1.0.8] - 2026-06-17 Resident Daemon Identity Preview

### Summary

Sayane v1.0.8 packages the resident daemon identity preview track. It adds a plan-only process identity contract and a read-only identity CLI preview for planned PID, lock, and socket paths without writing files, acquiring locks, creating sockets, or controlling a daemon process.

### Added

- Resident daemon process identity contract.
- Planned PID, lock, and socket paths.
- Runtime-local path validation for daemon identity paths.
- Read-only daemon identity CLI command:
  - `sayane app daemon-identity --json`
- Optional runtime directory override:
  - `sayane app daemon-identity --runtime-dir /path/to/runtime --json`
- Architecture docs for daemon identity contract and identity CLI preview.

### Security

- Identity preview does not write PID files.
- Identity preview does not acquire locks.
- Identity preview does not create sockets.
- Identity preview does not control processes.
- Path escape attempts are rejected by the app-layer identity model.

### Non-goals retained

- No production resident daemon process registry.
- No PID file writes.
- No lock acquisition.
- No stale lock cleanup.
- No OS service integration.

## [1.0.7] - 2026-06-17 Resident Daemon Lifecycle Preview

### Summary

Sayane v1.0.7 packages the resident daemon lifecycle preview track. It adds a lifecycle contract model, read-only daemon lifecycle CLI diagnostics, and plan-only daemon operation commands without starting a resident daemon or introducing production credentials.

### Added

- Resident daemon lifecycle contract model with explicit states:
  - `stopped`
  - `starting`
  - `running`
  - `stopping`
  - `failed`
- Resident daemon ownership modes:
  - `bridge_delegation`
  - `resident_server_reserved`
- Localhost-only bind validation for future resident daemon surfaces.
- Read-only lifecycle CLI commands:
  - `sayane app daemon-status --json`
  - `sayane app daemon-plan --json`
- Plan-only daemon operation CLI commands:
  - `sayane app daemon-start-plan --json`
  - `sayane app daemon-stop-plan --json`
  - `sayane app daemon-restart-plan --json`
- Architecture docs for lifecycle contract, lifecycle CLI, and operation plan commands.

### Security

- Daemon preview commands do not start, stop, restart, or expose a process.
- Local bind policy rejects non-localhost addresses.
- Bridge delegation remains the active serving path.

### Non-goals retained

- No production resident daemon.
- No OS service integration.
- No durable credentials.
- No vault unlock-session binding.
- No network-exposed resident API.

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

[Unreleased]: https://github.com/zyx-corporation/sayane/compare/v1.0.12...HEAD
[1.0.12]: https://github.com/zyx-corporation/sayane/compare/v1.0.11...v1.0.12
[1.0.11]: https://github.com/zyx-corporation/sayane/compare/v1.0.10...v1.0.11
[1.0.10]: https://github.com/zyx-corporation/sayane/compare/v1.0.9...v1.0.10
[1.0.9]: https://github.com/zyx-corporation/sayane/compare/v1.0.8...v1.0.9
[1.0.8]: https://github.com/zyx-corporation/sayane/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/zyx-corporation/sayane/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/zyx-corporation/sayane/compare/v1.0.3...v1.0.6
[1.0.3]: https://github.com/zyx-corporation/sayane/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/zyx-corporation/sayane/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/zyx-corporation/sayane/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/zyx-corporation/sayane/compare/v0.5.9...v1.0.0
