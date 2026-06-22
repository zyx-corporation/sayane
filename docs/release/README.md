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
- [v1.0.15 Operator Packaging and Supervision Phase Plan](v1.0.15-operator-packaging-supervision-phase-plan.md) — now tracks the implemented packaging / service-control / supervision / recovery-consent contract baselines plus remaining OS service decisions
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
- [v1.0.15 Post-App Follow-on Roadmap](v1.0.15-post-app-follow-on-roadmap.md) — current recommended order after the app-completion line
