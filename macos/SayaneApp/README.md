# Sayane macOS App Preview

This directory contains the first native macOS app shell for the Sayane resident app.

## Current scope

- native bootstrap and resident UI session recovery
- home overview
- home quick links and cross-screen navigation
- candidate queue / detail / diff / lineage
- queue filter/sort status strip and detail action-readiness summary
- cross-screen back navigation and visible navigation trail
- shared section/card/sheet primitives for consistent native layout
- review actions: evaluate / approve / reject / revise
- daemon and operator-phase panel
- daemon command copy, LaunchAgent plist inspection, and recovery preview summaries
- shared workspace status strip, loading states, and empty-state guidance
- shared state cards now carry recovery badges and inline next-action buttons for loading / empty / unavailable states
- daemon section navigator and expand/collapse controls for long operator screens
- connection diagnostics card with Bridge URL, health/debug-shell links, token/log paths, and recovery actions
- startup-oriented Bridge status panel with clear disconnected / starting / ready states
- compact Bridge status rail on Queue / Daemon so recovery actions stay visible away from Home
- shared action/result feedback banner for capture/review/copy flows, with sheet inputs preserved on failure
- candidate-specific result strip in Queue detail so the latest review outcome stays attached to the active candidate
- unified review command deck in Queue detail combining readiness, actions, and shortcut guidance
- start-here priority section on Home that promotes the next review item, quick link, and daemon action
- start-here focus section on Daemon that surfaces next action, LaunchAgent status, and runbook entry

## Build

```bash
swift build --package-path macos/SayaneApp
```

## Native smoke check

```bash
./scripts/check-macos-app-preview.sh
```

This runs the local Bridge shell, builds the Swift package, runs package tests,
and verifies the native app backend surfaces (`/health`, bearer-backed screen-state
routes, and cookie-backed `/app/ui` for the debug shell).

Useful options:

```bash
./scripts/check-macos-app-preview.sh --no-start
./scripts/check-macos-app-preview.sh --no-build --no-tests
./scripts/check-macos-app-preview.sh --verbose
```

- `--no-start` keeps a manually started Bridge and only checks the native-app surfaces
- `--no-build --no-tests` is useful when iterating on Bridge/session behavior only
- `--verbose` prints the last response body when a bootstrap or screen-state check fails

If the smoke check fails, inspect:

- Bridge log: `~/.sayane/macos-app-smoke.log`
- Cookie jar: `~/.sayane/macos-app-smoke.cookies.txt`
- Health check: `curl -s http://127.0.0.1:38741/health`
- Manual bootstrap: `open "http://127.0.0.1:38741/app/ui?bootstrap_token=$(cat ~/.sayane/bridge.token)"`

Common failure hints:

- `ERR_CONNECTION_REFUSED`: the Bridge is not listening; rerun the smoke script or start the Bridge first
- `Missing bootstrap bearer or valid resident app UI session`: the UI was opened without the bootstrap hop; reopen `/app/ui?bootstrap_token=...`
- `Missing or invalid resident app UI session`: the session cookie is stale; rerun the bootstrap URL or remove the cookie jar and retry

## Run from Xcode

```bash
xed macos/SayaneApp
```

Open the Swift package in Xcode, then run the `SayaneApp` executable target.

## Backend expectation

The app uses the local Bridge at:

```text
http://127.0.0.1:38741
```

Use the repo-level launcher first when needed:

```bash
./scripts/run-macos-app-preview.sh
```

If the app loses the Bridge connection after launch, use the native `Start Bridge` or `Reconnect` buttons from the error view.
The Home and error surfaces also expose one shared connection diagnostics card so the operator can
inspect the Bridge URL, health endpoint, debug shell URL, token path, and log path without leaving
the native app.
The Home screen also keeps a compact Bridge status panel above the rest of the content so initial
launch, reconnect, and log-first troubleshooting stay visible before drilling into Queue or Daemon.
Queue and Daemon also keep the same Bridge status surface in compact form so the operator can
recover connectivity without navigating back to Home first.
Capture / evaluate / approve / reject / revise / copy actions now report through one shared feedback
banner, and mutation sheets stay open on failure so the operator can retry without re-entering input.
Queue detail also keeps a candidate-specific result strip for the currently selected candidate when
the latest action affected that candidate.
The same Queue detail area now groups readiness badges, review actions, and shortcut hints into one
review command deck so the operator can decide and act without scanning multiple boxes.
Home also promotes the first review target, first quick link, and first daemon action into one
start-here section so the initial path is obvious after launch.
Daemon now mirrors that with a focus section that promotes the first next-action item, the current
LaunchAgent status, and the runbook entry point before the longer diagnostic sections.

The native daemon panel stays read-first. It exposes copyable CLI / `launchctl`
commands, lets the operator inspect the LaunchAgent plist and runtime directory,
and summarizes runtime-init / cleanup / repair previews without bypassing the
existing CLI-first mutation boundary.

It also surfaces the current operator packaging / supervision / recovery contract
directly from the daemon screen-state payload:

- packaging-model candidates and their blockers
- passive vs. active supervision boundaries
- background-surface candidates that remain deferred
- recommended recovery flow and app-UI guardrails
- cross-platform target context with the macOS LaunchAgent line kept explicit
- supported startup command, bootstrap UI, and phase-closure checklist visibility
- operator handoff snapshot with workstream states and recommended implementation order
- service lifecycle operations, policy gates, app-UI exposure limits, and governing rules
- LaunchAgent-specific runbook guidance: preflight, verification, log paths, security boundary, troubleshooting
- LaunchAgent plist preview, program arguments, and environment assumptions with copy support
- LaunchAgent preview metadata including operation id and preview hash for operator handoff
- stdout/stderr tail commands and preview/apply boundary reminders for recovery handoff
- LaunchAgent loaded status, return code, and stderr summary before deeper log inspection
- collapsible daemon sections with short summaries for faster scanning

The native app reads and writes the app-facing resident surfaces directly with the
local bearer token from `~/.sayane/bridge.token`.

The Bridge-hosted debug shell still uses:

```text
GET /app/ui?bootstrap_token=...
```

and then continues with the dedicated resident app UI session cookie.
