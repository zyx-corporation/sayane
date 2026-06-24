# Release Documents

This directory contains release notes, release closures, and release-prep documents for Sayane.

## Current release line

- [v1.0.13 Resident Daemon Preflight Schema Preview](v1.0.13-resident-daemon-preflight-schema-preview.md) — published release note
- [v1.0.13 Release Prep Checklist](v1.0.13-release-prep-checklist.md) — operator checklist
- [v1.0.13 Release Prep Issue Body](v1.0.13-release-prep-issue-body.md) — short reusable issue text
- [v1.0.13 Operator Handoff Note](v1.0.13-operator-handoff-note.md) — ready-to-use operator handoff

## Current app-facing handoff line

- [v1.0.14 Resident App Surface Handoff](v1.0.14-resident-app-surface-handoff.md) — UI implementation handoff for current resident app surfaces
- [v1.0.14 Resident App Surface Closure](v1.0.14-resident-app-surface-closure.md) — phase closeout for current resident app-facing integration slice
- [v1.0.14 Resident App Bootstrap UI Handoff](v1.0.14-resident-app-bootstrap-ui-handoff.md) — local HTML bootstrap UI handoff for current app-facing resident surfaces
- [v1.0.14 Resident App Bootstrap UI Closure](v1.0.14-resident-app-bootstrap-ui-closure.md) — phase closeout for the local HTML bootstrap UI slice
- [v1.0.14 UI Implementation Task Breakdown](v1.0.14-ui-implementation-task-breakdown.md) — next implementation tasks for the first UI slice
- [v1.0.14 UI Implementation Issue Breakdown](v1.0.14-ui-implementation-issue-breakdown.md) — issue-sized split for MVP and production completion
- [v1.0.14 UI Implementation Issue Templates](v1.0.14-ui-implementation-issue-templates.md) — GitHub-ready issue body templates for the same sequence
- [v1.0.14 UI Implementation Issue Title List](v1.0.14-ui-implementation-issue-title-list.md) — checklist-style titles and suggested labels for quick issue creation
- [v1.0.14 UI Implementation GitHub Issue Batch](v1.0.14-ui-implementation-github-issue-batch.md) — single batch document with titles, labels, and bodies for all 14 issues
- [v1.0.14 UI Implementation Issue Creation Checklist](v1.0.14-ui-implementation-issue-creation-checklist.md) — no-decision execution checklist for GitHub issue creation

## Current resident app UI decision line

- [ADR 0010 Resident App First Real UI Uses a Bridge-Hosted Local Web App Shell](../adr/0010-resident-app-first-real-ui-container.md) — accepted container decision for Issue 1 / the first real resident app UI shell
- [v1.0.14 Home Screen Design Note](v1.0.14-home-screen-design-note.md) — implementation-ready direction for Issue 2 using `GET /app/screen-state/home`
- [v1.0.14 Home Screen Implementation Skeleton](v1.0.14-home-screen-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 2
- [v1.0.14 Candidate Queue Design Note](v1.0.14-candidate-queue-design-note.md) — implementation-ready direction for Issue 3 using `GET /app/screen-state/candidates`
- [v1.0.14 Candidate Queue Implementation Skeleton](v1.0.14-candidate-queue-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 3
- [v1.0.14 Candidate Detail and Diff Design Note](v1.0.14-candidate-detail-diff-design-note.md) — implementation-ready direction for Issue 4 using `GET /app/screen-state/candidates/{id}` plus bounded diff preview
- [v1.0.14 Candidate Detail and Diff Implementation Skeleton](v1.0.14-candidate-detail-diff-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 4
- [v1.0.14 Candidate Action Flow Design Note](v1.0.14-candidate-action-flow-design-note.md) — implementation-ready direction for Issue 5 using existing app-facing write surfaces
- [v1.0.14 Candidate Action Flow Implementation Skeleton](v1.0.14-candidate-action-flow-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 5
- [v1.0.14 Clipboard Capture Entry Design Note](v1.0.14-clipboard-capture-entry-design-note.md) — implementation-ready direction for Issue 6 using `POST /app/capture-clipboard`
- [v1.0.14 Clipboard Capture Entry Implementation Skeleton](v1.0.14-clipboard-capture-entry-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 6
- [v1.0.14 Daemon Panel Design Note](v1.0.14-daemon-panel-design-note.md) — implementation-ready direction for Issue 7 using `GET /app/screen-state/daemon`
- [v1.0.14 Daemon Panel Implementation Skeleton](v1.0.14-daemon-panel-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 7
- [v1.0.14 MVP UI State Handling and Regression Design Note](v1.0.14-mvp-ui-state-handling-design-note.md) — implementation-ready direction for Issue 8 shared state handling and focused regression coverage
- [v1.0.14 MVP UI State Handling and Regression Implementation Skeleton](v1.0.14-mvp-ui-state-handling-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 8
- [v1.0.14 Production Auth Model Design Note](v1.0.14-production-auth-model-design-note.md) — implementation-ready direction for Issue 9 separating bootstrap bearer entry from steady-state UI session behavior
- [v1.0.14 Production Auth Model Implementation Skeleton](v1.0.14-production-auth-model-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 9
- [v1.0.14 Final Interaction and Visual System Design Note](v1.0.14-final-interaction-visual-system-design-note.md) — implementation-ready direction for Issue 10 final navigation, accessibility, responsiveness, and visual language
- [v1.0.14 Final Interaction and Visual System Implementation Skeleton](v1.0.14-final-interaction-visual-system-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 10
- [v1.0.14 Extension and App Surface Alignment Design Note](v1.0.14-extension-app-surface-alignment-design-note.md) — implementation-ready direction for Issue 11 shared semantics and explicit surface split
- [v1.0.14 Extension and App Surface Alignment Implementation Skeleton](v1.0.14-extension-app-surface-alignment-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 11
- [v1.0.14 Real UI E2E and Regression Design Note](v1.0.14-real-ui-e2e-regression-design-note.md) — implementation-ready direction for Issue 12 GUI-level operator-path regression
- [v1.0.14 Real UI E2E and Regression Implementation Skeleton](v1.0.14-real-ui-e2e-regression-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 12
- [v1.0.14 Release and Operator Readiness Design Note](v1.0.14-release-operator-readiness-design-note.md) — implementation-ready direction for Issue 13 startup/config/log/runbook readiness
- [v1.0.14 Release and Operator Readiness Implementation Skeleton](v1.0.14-release-operator-readiness-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 13
- [v1.0.14 Resident App Operator Handoff](v1.0.14-resident-app-operator-handoff.md) — operator-ready startup, config, diagnostics, and troubleshooting handoff for the current resident app shell
- [v1.0.14 Non-MVP Boundary Resolution Design Note](v1.0.14-non-mvp-boundary-resolution-design-note.md) — implementation-ready direction for Issue 14 explicit defer and separate-plan decisions
- [v1.0.14 Non-MVP Boundary Resolution Implementation Skeleton](v1.0.14-non-mvp-boundary-resolution-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for Issue 14

## Resident daemon preview line

- [v1.0.12 Resident Daemon Policy Gate](v1.0.12-resident-daemon-policy-gate.md)
- [v1.0.11 Resident Daemon PID File Diagnostic Preview](v1.0.11-resident-daemon-pid-file-diagnostic-preview.md)
- [v1.0.10 Resident Daemon Cleanup Decision Preview](v1.0.10-resident-daemon-cleanup-decision-preview.md)
- [v1.0.9 Resident Daemon Runtime Layout Preview](v1.0.9-resident-daemon-runtime-layout-preview.md)
- [v1.0.8 Resident Daemon Identity Preview](v1.0.8-resident-daemon-identity-preview.md)
- [v1.0.7 Resident Daemon Lifecycle Preview](v1.0.7-resident-daemon-lifecycle-preview.md)
- [v1.0.6 Resident Foundation](v1.0.6-resident-foundation.md)

## Broader release / closure documents

- [v1.0.15 Post-App Follow-on Roadmap](v1.0.15-post-app-follow-on-roadmap.md) — prioritized roadmap after the resident app local-shell completion line
- [v1.0.15 Resident Daemon Proof Phase Plan](v1.0.15-resident-daemon-proof-phase-plan.md) — separate future plan for daemon identity/readiness/API proof work
- [v1.0.15 Resident Daemon Proof Design Note](v1.0.15-resident-daemon-proof-design-note.md) — implementation-ready direction for the first daemon proof phase
- [v1.0.15 Resident Daemon Proof Implementation Skeleton](v1.0.15-resident-daemon-proof-implementation-skeleton.md) — file-touch, acceptance, and test-plan skeleton for the daemon proof phase
- [v1.0.15 Resident Daemon Proof Issue Breakdown](v1.0.15-resident-daemon-proof-issue-breakdown.md) — issue-sized split for identity/readiness/API proof work
- [v1.0.15 Release Note](v1.0.15-release-note.md) — proof-oriented diagnostics release closure for the resident daemon proof line
- [v1.0.15 Operator Packaging and Supervision Phase Plan](v1.0.15-operator-packaging-supervision-phase-plan.md) — now tracks the implemented packaging / service-control / supervision / recovery-consent contract baselines plus remaining OS service decisions
- [v1.0.16 Operator Observation Alignment Release Note](v1.0.16-operator-observation-alignment-release-note.md) — aligns CLI, bridge-hosted shell, native preview, and operator docs around the current observation-only operator line
- [v1.0.17 Implementation Gate Visibility Release Note](v1.0.17-implementation-gate-visibility-release-note.md) — adds schema-only implementation-gate preflight visibility to the same operator read stack
- [v1.0.18 Service Target Gate Visibility Release Note](v1.0.18-service-target-gate-visibility-release-note.md) — exposes service-target policy gates more clearly in the bridge-hosted daemon shell and launcher guidance
- [v1.0.19 Bridge Operator Drill-Down Release Note](v1.0.19-bridge-operator-drilldown-release-note.md) — adds dedicated browser and token-backed daemon drill-down reads plus matching daemon-shell navigation
- [v1.0.20 Bridge Decision Assist Release Note](v1.0.20-bridge-decision-assist-release-note.md) — adds next-command guidance cards to the bridge-hosted daemon shell
- [v1.0.21 Bridge Phase Closure Gate Guide Release Note](v1.0.21-bridge-phase-closure-gate-guide-release-note.md) — maps unfinished phase-closure gates to the exact daemon read surface that clarifies them
- [v1.0.22 Bridge Preflight Gate Integration Release Note](v1.0.22-bridge-preflight-gate-integration-release-note.md) — integrates schema-only implementation-gate preflight into the bridge-hosted daemon read stack
- [v1.0.23 Bridge Operator Summary Rail Release Note](v1.0.23-bridge-operator-summary-rail-release-note.md) — groups the current gate, next command, and next read surface into one compact browser rail
- [v1.0.24 Native Operator Summary Rail Release Note](v1.0.24-native-operator-summary-rail-release-note.md) — brings the same operator-orientation rail to the native macOS daemon screen
- [v1.0.25 Native Start Here Navigation Release Note](v1.0.25-native-start-here-navigation-release-note.md) — turns native Daemon `Start Here` cards into direct section navigation
- [v1.0.26 Native Priority Section Navigation Release Note](v1.0.26-native-priority-section-navigation-release-note.md) — splits native Daemon section navigation into priority and remaining sections
- [v1.0.27 Native Remaining Workstreams Release Note](v1.0.27-native-remaining-workstreams-release-note.md) — leaves only non-priority workstreams in native Daemon workspace cards
- [v1.0.28 Native Priority Review Order Release Note](v1.0.28-native-priority-review-order-release-note.md) — aligns deeper native Daemon review blocks with the same priority path
- [v1.0.29 Native LaunchAgent Current State Release Note](v1.0.29-native-launchagent-current-state-release-note.md) — keeps LaunchAgent current state and recovery previews together in native Daemon
- [v1.0.30 Native LaunchAgent Runbook Order Release Note](v1.0.30-native-launchagent-runbook-order-release-note.md) — aligns native LaunchAgent Runbook with the same health-first read order
- [v1.0.31 Native LaunchAgent Command Deck Order Release Note](v1.0.31-native-launchagent-command-deck-order-release-note.md) — aligns native LaunchAgent command deck with the same inspect-first read order
- [v1.0.32 Native LaunchAgent Command Groups Release Note](v1.0.32-native-launchagent-command-groups-release-note.md) — makes native LaunchAgent inspect and recover groups match their actual operator intent
- [v1.0.33 Native LaunchAgent Command Group Summaries Release Note](v1.0.33-native-launchagent-command-group-summaries-release-note.md) — adds short intent summaries to each native LaunchAgent command group
- [v1.0.34 Native LaunchAgent Focus Release Note](v1.0.34-native-launchagent-focus-release-note.md) — adds a compact first-glance focus block to the native LaunchAgent section
- [v1.1.0 Release Note](v1.1.0-release-note.md)
- [v1.1 Scoped Context Closure](v1.1-scoped-context-closure.md)
- [v1.0.0 Context Acceptance](v1.0.0-context-acceptance.md)
- [Phase 6-17 Release Closure](phase6-17-release-closure.md)

## Current post-app operator line

The current post-app completion line is not phase closure for OS service integration or background
supervision. It is a handoff-ready read surface for the next operator-facing phase.

Use these documents first:

- [v1.0.14 Resident App Operator Handoff](v1.0.14-resident-app-operator-handoff.md) — current startup, diagnostics, troubleshooting, and read-surface guidance
- [v1.0.15 Operator Packaging and Supervision Phase Plan](v1.0.15-operator-packaging-supervision-phase-plan.md) — current packaging / service / supervision / recovery phase baseline and remaining gates
- [v1.0.16 Operator Observation Alignment Release Note](v1.0.16-operator-observation-alignment-release-note.md) — current aligned browser/native/operator-doc observation release without phase-closure claims
- [v1.0.17 Implementation Gate Visibility Release Note](v1.0.17-implementation-gate-visibility-release-note.md) — current operator read stack now also includes the schema-only implementation gate preview
- [v1.0.18 Service Target Gate Visibility Release Note](v1.0.18-service-target-gate-visibility-release-note.md) — current operator read stack now surfaces hybrid/service-target gate blockers more explicitly
- [v1.0.19 Bridge Operator Drill-Down Release Note](v1.0.19-bridge-operator-drilldown-release-note.md) — current bridge-hosted daemon shell now links directly into focused operator drill-down reads
- [v1.0.20 Bridge Decision Assist Release Note](v1.0.20-bridge-decision-assist-release-note.md) — current bridge-hosted daemon shell now suggests the next read command from the same operator workspace
- [v1.0.21 Bridge Phase Closure Gate Guide Release Note](v1.0.21-bridge-phase-closure-gate-guide-release-note.md) — current bridge-hosted daemon shell now maps unfinished gates to the read surface that clarifies each one
- [v1.0.22 Bridge Preflight Gate Integration Release Note](v1.0.22-bridge-preflight-gate-integration-release-note.md) — current bridge-hosted daemon shell now includes implementation-gate preflight in the same drill-down and gate-guide workflow
- [v1.0.23 Bridge Operator Summary Rail Release Note](v1.0.23-bridge-operator-summary-rail-release-note.md) — current bridge-hosted daemon shell now surfaces the first operator orientation cues in one compact rail
- [v1.0.24 Native Operator Summary Rail Release Note](v1.0.24-native-operator-summary-rail-release-note.md) — current native macOS daemon screen now mirrors that same compact operator orientation rail
- [v1.0.25 Native Start Here Navigation Release Note](v1.0.25-native-start-here-navigation-release-note.md) — current native macOS daemon screen now lets `Start Here` jump directly into the matching operator section
- [v1.0.26 Native Priority Section Navigation Release Note](v1.0.26-native-priority-section-navigation-release-note.md) — current native macOS daemon screen now keeps section navigation aligned with the same priority path
- [v1.0.27 Native Remaining Workstreams Release Note](v1.0.27-native-remaining-workstreams-release-note.md) — current native macOS daemon workspace now avoids repeating surfaces already covered by the priority path above
- [v1.0.28 Native Priority Review Order Release Note](v1.0.28-native-priority-review-order-release-note.md) — current native macOS daemon deeper-review blocks now follow that same priority path order
- [v1.0.29 Native LaunchAgent Current State Release Note](v1.0.29-native-launchagent-current-state-release-note.md) — current native macOS LaunchAgent checks now keep current state and recovery previews in one read-first section
- [v1.0.30 Native LaunchAgent Runbook Order Release Note](v1.0.30-native-launchagent-runbook-order-release-note.md) — current native macOS LaunchAgent Runbook now starts with health checks before logs and preview detail
- [v1.0.31 Native LaunchAgent Command Deck Order Release Note](v1.0.31-native-launchagent-command-deck-order-release-note.md) — current native macOS LaunchAgent command deck now places recovery before start actions
- [v1.0.32 Native LaunchAgent Command Groups Release Note](v1.0.32-native-launchagent-command-groups-release-note.md) — current native macOS LaunchAgent inspect group is non-mutating and recover now orders cleanup / repair / bootout
- [v1.0.33 Native LaunchAgent Command Group Summaries Release Note](v1.0.33-native-launchagent-command-group-summaries-release-note.md) — current native macOS LaunchAgent command deck now explains each group before showing commands
- [v1.0.34 Native LaunchAgent Focus Release Note](v1.0.34-native-launchagent-focus-release-note.md) — current native macOS LaunchAgent section now starts with current state, recovery preview, and next command together
- [v1.0.35 Native LaunchAgent Detail Split Release Note](v1.0.35-native-launchagent-detail-split-release-note.md) — current native macOS LaunchAgent summary stays compact while lower groups focus on verification details
- [v1.0.36 Native Local Launcher and Smoke Reliability Release Note](v1.0.36-native-local-launcher-and-smoke-reliability-release-note.md) — current native app launcher prefers Chrome bootstrap and smoke uses a fast filtered Swift test
- [v1.0.37 Native Direct Preview Launch Release Note](v1.0.37-native-direct-preview-launch-release-note.md) — current native app preview now launches directly from the built executable without requiring Xcode by default
- [v1.0.38 Native Queue Detail Copy Actions Release Note](v1.0.38-native-queue-detail-copy-actions-release-note.md) — current native queue detail view now copies detail, diff, and lineage directly to the clipboard
- [v1.0.39 Native LaunchAgent Copy Actions Release Note](v1.0.39-native-launchagent-copy-actions-release-note.md) — current native LaunchAgent detail groups now copy state and recovery preview text directly to the clipboard
- [v1.0.40 Native Daemon Handoff Copy Actions Release Note](v1.0.40-native-daemon-handoff-copy-actions-release-note.md) — current native Daemon summary, gate, action, and evidence blocks now copy handoff-ready text directly to the clipboard
- [v1.0.41 Native Daemon Handoff Export Release Note](v1.0.41-native-daemon-handoff-export-release-note.md) — current native Daemon header now exports one combined handoff text file directly from the app
- [v1.0.42 Native Daemon Handoff Evidence Metadata Release Note](v1.0.42-native-daemon-handoff-evidence-metadata-release-note.md) — current native Daemon handoff export now includes generation time and Bridge context metadata
- [v1.0.43 Native Daemon Handoff Timestamped Artifact Release Note](v1.0.43-native-daemon-handoff-timestamped-artifact-release-note.md) — current native Daemon export now uses timestamped filenames and captures Bridge version/source freshness
- [v1.0.44 Native Daemon Handoff Diagnostic Paths Release Note](v1.0.44-native-daemon-handoff-diagnostic-paths-release-note.md) — current native Daemon export now includes component identity and local token/log paths
- [v1.0.45 Native Daemon Handoff Debug Shell and Next Action Release Note](v1.0.45-native-daemon-handoff-debug-shell-and-next-action-release-note.md) — current native Daemon export now includes the debug-shell URL and first next-action summary
- [v1.0.46 Native Daemon Handoff CLI Diagnostics Release Note](v1.0.46-native-daemon-handoff-cli-diagnostics-release-note.md) — current native Daemon export now includes launchctl print and stdout/stderr tail commands
- [v1.0.47 Native Daemon Handoff Preflight and Proof Entry Release Note](v1.0.47-native-daemon-handoff-preflight-proof-release-note.md) — current native Daemon export now includes preflight and proof-diagnostics entry commands
- [v1.0.48 Native Daemon Handoff Sectioned Diagnostics Release Note](v1.0.48-native-daemon-handoff-sectioned-diagnostics-release-note.md) — current native Daemon export now groups inspect, log, preflight, and proof entry commands more clearly
- [v1.0.49 Native Daemon Handoff Section Headers Release Note](v1.0.49-native-daemon-handoff-section-headers-release-note.md) — current native Daemon export now applies explicit section headers across later operator and LaunchAgent blocks
- [v1.0.50 Native Daemon Handoff Operator Flow Order Release Note](v1.0.50-native-daemon-handoff-operator-flow-order-release-note.md) — current native Daemon export now orders the later sections to follow the operator flow more closely
- [v1.0.51 Native Daemon Handoff Bridge Context Release Note](v1.0.51-native-daemon-handoff-bridge-context-release-note.md) — current native Daemon export now wraps the opening metadata block in an explicit Bridge Context section
- [v1.0.52 Native Daemon Handoff Bridge Context I18n Release Note](v1.0.52-native-daemon-handoff-bridge-context-i18n-release-note.md) — current native Daemon export now localizes the Bridge Context header itself
- [v1.0.53 Native Daemon Handoff Diagnostic Label I18n Release Note](v1.0.53-native-daemon-handoff-diagnostic-label-i18n-release-note.md) — current native Daemon export now localizes diagnostic section labels consistently
- [v1.0.54 Native Daemon Handoff CLI Label I18n Release Note](v1.0.54-native-daemon-handoff-cli-label-i18n-release-note.md) — current native Daemon export now localizes CLI label text such as `launchctl print` and log tails
- [v1.0.55 Native Smoke Full Test Default Release Note](v1.0.55-native-smoke-full-test-default-release-note.md) — current native smoke script now validates with the full Swift Testing suite by default and skips the hanging XCTest path
- [v1.0.56 Resident App UI Session Smoke Release Note](v1.0.56-resident-app-ui-session-smoke-release-note.md) — current bridge-hosted local shell now has a direct UI-session smoke path outside full pytest
- [v1.0.57 Resident App API Surface Smoke Release Note](v1.0.57-resident-app-api-surface-smoke-release-note.md) — current bearer-backed app-facing JSON read surfaces now have a direct smoke path outside full pytest
- [v1.0.58 Resident App Release Smoke Wrapper Release Note](v1.0.58-resident-app-release-smoke-wrapper-release-note.md) — current release verification now has one wrapper for API surface and UI session smoke
- [v1.0.59 Resident App Smoke CLI Bridge Start Release Note](v1.0.59-resident-app-smoke-cli-bridge-start-release-note.md) — current smoke scripts now start the Bridge through the same `sayane serve` CLI path used by operators
- [v1.0.60 Resident App Smoke Venv CLI Preference Release Note](v1.0.60-resident-app-smoke-venv-cli-preference-release-note.md) — current smoke scripts now prefer the repo-local CLI install over user-local shims during Bridge startup
- [v1.0.61 Resident App CLI Serve Watchfiles Guard Release Note](v1.0.61-resident-app-cli-serve-watchfiles-guard-release-note.md) — current CLI/local-launch path now avoids broken optional `watchfiles` imports and clears stale detached `serve` processes before restart
- [v1.0.62 Native Smoke Launcher Alignment Release Note](v1.0.62-native-smoke-launcher-alignment-release-note.md) — current native preview smoke now shares the same Bridge launcher path, stale-process cleanup, and timeout budget as the resident app shell
- [v1.0.63 Resident App Full Release Smoke Release Note](v1.0.63-resident-app-full-release-smoke-release-note.md) — current one-command release smoke now covers API, UI session, and native preview together with launcher retry protection
- [v1.0.64 Isolated Package Metadata Check Release Note](v1.0.64-isolated-package-metadata-check-release-note.md) — current local release-prep build path now verifies package metadata inside a short-lived isolated toolchain instead of depending on a damaged long-lived `nh3` install
- [v1.0.15 Post-App Follow-on Roadmap](v1.0.15-post-app-follow-on-roadmap.md) — current recommended order after the app-completion line
