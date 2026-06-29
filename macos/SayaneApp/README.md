# Sayane macOS App

This directory contains the current primary native macOS app for the Sayane resident app.

Platform focus for the current line:

- macOS is the active completion target
- Linux keeps the recorded `systemd --user` shipped slice, but further packaging work is paused
- Windows keeps the recorded contract-only target state, but implementation work is paused

## Current scope

- native bootstrap and resident UI session recovery
- home overview
- home quick links and cross-screen navigation
- candidate queue / detail / diff / lineage
- meaningful evaluation-level labels in native queue/detail and review sheet
- queue filter/sort status strip and detail action-readiness summary
- queue section filters and quick-filter chips now localize resident section names consistently
- Home priority review summary and Queue lineage details now also localize resident/status values instead of leaking raw tokens
- Home quick links now explain destination intent instead of showing raw paths, and Queue lineage timestamps render as relative plus absolute time
- Queue lineage cards now prefer localized event/status/section summaries over raw payload summary text
- Queue lineage tone badges now derive from explicit event/status meaning instead of substring matching
- Queue lineage detail rows are now ordered semantically: event/status, section context, timestamps, then IDs
- Daemon helper summaries are now shorter, while keeping the same decision and inspection meaning
- Home and Daemon command badges now share one command-priority helper for consistent tone and wording
- Daemon workspace, gate, decision, and evidence cards now share one command-action block for open/copy behavior
- Queue review readiness badges and action buttons now share one data model, reducing drift between availability and action wiring
- Home and Daemon cards now share a small title-summary view for consistent heading hierarchy
- Queue summary rows and Lineage detail rows now share one label-value row style
- Daemon plain label-value rows are also moving onto the same shared row style
- Daemon badge-bearing label-value rows now also share a common row style
- Home and Daemon summary cards now share one value presenter, including string and boolean badge handling
- Daemon command rows and bullet lists now also share small reusable views, keeping copy/read formatting aligned
- Daemon operator summaries and runbook-style bullet groups now reuse the same bullet-list presenter
- Bridge diagnostics, error text, and LaunchAgent read surfaces now also share one selectable monospace presenter
- LaunchAgent Runbook now also exposes proof-oriented CLI diagnostics while keeping daemon wording preview-oriented
- cross-screen back navigation and visible navigation trail
- shared section/card/sheet primitives for consistent native layout
- review actions: evaluate / approve / reject / revise
- daemon and operator-phase panel
- daemon command copy, LaunchAgent plist inspection, and recovery preview summaries
- shared workspace status strip, loading states, and empty-state guidance
- shared state cards now carry recovery badges and inline next-action buttons for loading / empty / unavailable states
- daemon section navigator and expand/collapse controls for long operator screens
- connection diagnostics card with Bridge URL, health/debug-shell links, token/log paths, and recovery actions
- debug-only compatibility shell actions are now kept in the diagnostics sheet instead of the routine operator cards
- startup-oriented Bridge status panel with clear disconnected / starting / ready states
- compact Bridge status rail on Queue / Daemon so recovery actions stay visible away from Home
- shared action/result feedback banner for capture/review/copy flows, with sheet inputs preserved on failure
- candidate-specific result strip in Queue detail so the latest review outcome stays attached to the active candidate
- unified review command deck in Queue detail combining readiness, actions, and shortcut guidance
- start-here priority section on Home that promotes the next review item, quick link, and daemon action
- start-here focus section on Daemon that surfaces next action, LaunchAgent status, and runbook entry
- operator summary rail on Daemon that keeps current gate / next command / next read surface together near the top
- start-here cards on Daemon now jump directly into the matching LaunchAgent / runbook / operator section
- section navigator on Daemon now separates priority sections from the remaining sections to match the same top-of-screen operator path
- LaunchAgent status and runbook now appear near the top of Daemon so the first operational checks stay close to Start Here
- Daemon opens LaunchAgent runbook by default, while the heavier Operator Phase detail starts collapsed to reduce first-load density
- daemon next-epic workspace that condenses packaging / service / supervision / recovery status into one operator decision surface
- short guidance captions on daemon workspace sections so operators can tell what to inspect next at a glance
- dense status panels now preview representative commands and summarize the remaining items before the full detail
- status panels are now ordered from packaging/service/recovery toward supervision/operator-phase so the likely decision path reads top-down
- highlight badges inside status panels are also ordered from blockers/review-needed toward ready/available states
- phase-closure gate cards that map unresolved operator-phase checklist items to the exact packaging / service / supervision / recovery read surface
- recommended implementation order and phase-checklist snippets stay visible in that workspace so operators can see both sequence and blockers before diving deeper
- evidence drill-down cards keep the aligned daemon JSON read surfaces one click away from the same workspace
- each evidence card also carries a small current-status snapshot so operators can compare surfaces before opening deeper sections
- decision-assist cards now suggest the next service-control, recovery, or supervision read/control command directly from the same daemon workspace
- launchagent-adjacent decision assist now also routes runtime-init, cleanup-preview, and repair-preview review from the same workspace
- workspace cards compress blocker display to the primary blocker plus remaining-count, then keep the next command directly underneath
- Home daemon action cards now use the same summary-then-command order as the daemon workspace, and Queue review actions use a denser 2-column action grid
- Root sidebar now behaves more like a native compact navigator: non-selected rows hide secondary summary text, while the top status strip uses badges instead of long inline labels
- Home summary cards now stay capped to a short preview with remaining-count, keeping the launcher path above the fold
- Queue left pane now keeps reviewable-count, active-filter count, sort mode, and aggregate chips in a shorter chrome stack
- Queue detail header now promotes candidate id, current status, section, and evaluation badges before the lower evidence blocks
- candidate action sheets now keep candidate identity visible in-sheet and bias toward shorter right-aligned native action rows
- diagnostics sheet now opens with one compact troubleshooting header plus current bridge-state badge, and its action rows wrap naturally on narrower widths
- Daemon summary cards now preview only the top set, and status panels now collapse to representative status/highlight/command cards before deeper drill-down

## Build

```bash
swift build --package-path macos/SayaneApp
```

## Package / Install

Current macOS distribution stays local-first:

- the main user install path still starts with `curl | bash` for CLI / Bridge
- build the native `.app` bundle from the current checkout
- keep the local CLI / Bridge runtime as the current backend prerequisite
- install the app into `~/Applications` for operator use

Create a distributable bundle:

```bash
bash scripts/build-macos-app-bundle.sh
# or also emit a zip archive:
bash scripts/build-macos-app-bundle.sh --zip
```

Generated artifacts now include:

- `dist/macos/SayaneApp.app`
- `dist/macos/SayaneApp-<version>-macos-release.zip`
- `dist/macos/SayaneApp-latest-macos-release.zip`
- `dist/macos/SayaneApp-<version>-macos-release.sha256`
- `dist/macos/SayaneApp-<version>-macos-release.manifest.txt`

Install into `~/Applications`:

```bash
bash scripts/install-macos-app.sh
bash scripts/refresh-macos-app.sh
```

Remove from `~/Applications`:

```bash
bash scripts/uninstall-macos-app.sh
```

Useful options:

```bash
bash scripts/build-macos-app-bundle.sh --debug
bash scripts/install-macos-app.sh --no-build
bash scripts/install-macos-app.sh --applications /tmp/SayaneApps
bash scripts/refresh-macos-app.sh --no-build
bash scripts/refresh-macos-app.sh --debug --no-open
bash scripts/install-macos-app.sh --no-adhoc-sign
```

Default paths:

- bundle output: `dist/macos/SayaneApp.app`
- local install target: `~/Applications/SayaneApp.app`

Quick verification:

```bash
bash scripts/verify-macos-app-install.sh
plutil -lint ~/Applications/SayaneApp.app/Contents/Info.plist
file ~/Applications/SayaneApp.app/Contents/MacOS/SayaneApp
open ~/Applications/SayaneApp.app
```

Boundary notes:

- current primary install path is still `curl | bash` for CLI / Bridge
- current packaging is **not** a notarized dmg or signed pkg flow yet
- current app launch now prefers an installed `sayane` CLI (`~/.local/bin/sayane`, `PATH`, or `SAYANE_CLI_BIN`) before falling back to repo-local launch scripts
- installed `.app` bundles now carry `Contents/Resources/run-bridge-helper.sh` so normal app startup no longer depends on repo-local launchers
- current app install still expects the local Sayane CLI / Bridge runtime to exist
- use `docs/install.md` as the operator-facing install entrypoint
- native diagnostics now surface the launch source (`bundled_helper`, `installed_cli`, or `repo_launcher`) and the last launch failure directly inside the app
- local install now applies an ad-hoc signature so `open ~/Applications/SayaneApp.app` works before maintainer signing/notarization is available

Signing / notarization preparation:

```bash
bash scripts/sign-macos-app.sh --dry-run --identity "Developer ID Application: Example"
bash scripts/notarize-macos-app.sh --dry-run --profile sayane-notary
bash scripts/prepare-macos-release-artifacts.sh
```

When maintainer secrets are available, the same helpers can be used for the real
`codesign` / `notarytool` flow with:

- `SAYANE_MACOS_CODESIGN_IDENTITY`
- `SAYANE_MACOS_NOTARY_PROFILE`
- optional `SAYANE_MACOS_TEAM_ID`
- optional `SAYANE_MACOS_APPLE_ID`

## Native smoke check

```bash
./scripts/check-macos-app-preview.sh
```

This runs the local Bridge shell, builds the Swift package, runs package tests,
and verifies the native app backend surfaces (`/health` and bearer-backed screen-state
routes). Debug-shell compatibility checks are optional.

Useful options:

```bash
./scripts/check-macos-app-preview.sh --no-start
./scripts/check-macos-app-preview.sh --no-build --no-tests
./scripts/check-macos-app-preview.sh --bridge-background
./scripts/check-macos-app-preview.sh --bridge-terminal
./scripts/check-macos-app-preview.sh --with-debug-shell
./scripts/check-macos-app-preview.sh --verbose
```

- `--no-start` keeps a manually started Bridge and only checks the native-app surfaces
- `--no-build --no-tests` is useful when iterating on Bridge/session behavior only
- `--bridge-background` forces a permission-free background Bridge launch during smoke
- `--bridge-terminal` forces the Terminal-window launch path when that behavior itself is under test
- default behavior runs the full `swift test --package-path macos/SayaneApp --disable-xctest` suite during smoke validation
- default `auto` mode now retries with a background Bridge launch if macOS denies Terminal Apple Events
- `--with-debug-shell` additionally validates `/app/ui` bootstrap and cookie-backed compatibility flows
- `--verbose` prints the last response body when a bootstrap or screen-state check fails

If the native-first smoke check fails, inspect:

- Bridge log: `~/.sayane/macos-app-smoke.log`
- Cookie jar: `~/.sayane/macos-app-smoke.cookies.txt`
- Health check: `curl -s http://127.0.0.1:38741/health`
- Debug-shell bootstrap only when native diagnostics are insufficient: `open -a "Google Chrome" "http://127.0.0.1:38741/app/ui?bootstrap_token=$(cat ~/.sayane/bridge.token)"`

Common failure hints:

- `ERR_CONNECTION_REFUSED`: the Bridge is not listening; rerun the smoke script or start the Bridge first
- `Missing bootstrap bearer or valid resident app UI session`: only relevant for the debug-only compatibility shell; reopen `/app/ui?bootstrap_token=...` if that shell is explicitly under test
- `Missing or invalid resident app UI session`: only relevant for the debug-only compatibility shell; rerun the bootstrap URL or remove the cookie jar and retry

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

Normal macOS operator startup should come from the installed native app itself once the local CLI is installed.

Repo-local launchers remain the development fallback:

```bash
./scripts/run-macos-app-preview.sh
```

Installed app bundles use the bundled helper first:

```text
~/Applications/SayaneApp.app/Contents/Resources/run-bridge-helper.sh
```

Useful options:

```bash
./scripts/run-macos-app-preview.sh --no-build
./scripts/run-macos-app-preview.sh --foreground
./scripts/run-macos-app-preview.sh --bridge-terminal
./scripts/run-macos-app-preview.sh --bridge-background
./scripts/run-macos-app-preview.sh --xcode
```

- default mode starts or reuses the local Bridge, then launches the built native executable directly
- on macOS, the default Bridge launcher prefers a dedicated Terminal window over an in-process detached background launch
- `--bridge-terminal` / `--bridge-background` / `--bridge-foreground` pin the Bridge start mode when auto mode is not what you want
- `--no-build` reuses the current debug executable when iterating on launch behavior
- `--foreground` keeps the native process attached to the current terminal
- `--xcode` falls back to the old Package.swift-in-Xcode path when manual IDE inspection is needed
- the launcher now fails closed unless it finds a compatible Python (`>=3.11` + Sayane deps); run
  `uv run --extra dev pytest -q` once or prepare `.venv` first if the local machine is not primed yet

If the app loses the Bridge connection after launch, use the native `Start Bridge` or `Reconnect` buttons from the error view.
The Home and error surfaces also expose one shared connection diagnostics card so the operator can
inspect the Bridge URL, health endpoint, browser-compatibility entry, token path, and log path without leaving
the native app.
When the app is disconnected on macOS, the recovery copy now explicitly assumes the Terminal-backed
Bridge path: start the Bridge, keep that Terminal window open, and then reconnect from the app.
Successful `Start Bridge`, `Reconnect`, and `Refresh` actions now also raise a native feedback banner
so the operator can tell whether recovery actually completed without leaving the current screen.
Those same recovery actions now show an in-progress banner first, and failed recovery banners point
back to the Bridge Terminal window plus `~/.sayane/run-app-local.log`.
While that recovery is running, the main recovery buttons are disabled so repeated clicks do not
queue overlapping Bridge actions.
The main recovery button label also switches to an in-progress form such as `Bridge 起動中…` or
`再接続中…` while that work is active.
The Bridge status panel and compact error recovery card also show a spinner during that same window,
and launcher / compatibility-open actions are temporarily disabled until recovery finishes.
The top feedback banner now mirrors that state too, adding a small spinner next to the status badge
for in-progress recovery messages.
The toolbar `Refresh` action also follows that same state, switching its label to the active
recovery wording and disabling itself while recovery is still running.
Where the startup command resolves to a local script path, the native recovery surfaces now also expose
`Open Launcher` beside `Copy Startup Command`. Browser compatibility actions stay in the diagnostics
sheet instead of the routine operator cards. When the local token file is available, those debug
actions prefer the bootstrap URL automatically instead of opening raw `/app/ui` first.
The error view now also keeps one compact recovery card first, so the operator can trigger the
recommended recovery action, copy the startup command, and open logs before reading deeper diagnostics.
That diagnostics card now stays reference-first: it keeps file paths, URLs, and debug/compatibility-only
utilities together, while the Bridge status panel carries the main recovery and navigation actions.
The Home screen also keeps a compact Bridge status panel above the rest of the content so initial
launch, reconnect, and log-first troubleshooting stay visible before drilling into Queue or Daemon.
That same Home/Bridge Status surface now uses the same startup/debug actions as the Daemon supported-path
and compact error surfaces, so operators do not need to remember a separate recovery path per screen.
Queue and Daemon also keep the same Bridge status surface in compact form so the operator can
recover connectivity without navigating back to Home first.
When daemon state is available, the same native recovery surfaces now also show the current startup
command directly, so the operator can copy the local restart path without opening the browser compatibility shell.
The same Bridge status area now also surfaces the current gate and first next command from daemon
state, so phase-closure blockers and the next local CLI step stay visible before opening the deeper
Daemon workspace.
It now also keeps the first next read surface nearby, so the operator can see which local evidence
command to inspect next without scanning the longer daemon sections.
Because that daemon guidance now lives in the Bridge status area, `Start Here` on Home can stay
focused on review and quick-link entry points instead of repeating the same daemon summary twice.
The deeper daemon detail groups now also trim long lists down to short previews plus remaining-count
markers, so the lower half reads more like supporting evidence than a second summary rail.
Within LaunchAgent detail, the command deck now stays action-first while the runbook keeps the
proof/preflight/log-reference material, reducing repeated open/copy controls across both sections.
The queue detail screen now follows the same pattern: the review command deck stays action-first,
while a separate evidence drill-down block groups the detail / diff / lineage copy surfaces.
The queue left pane now also folds status counts and top sections into one compact status bar, so
the quick filters stay interactive without repeating the same aggregate lists underneath.
The search/filter split is now clearer too: `Filters` handles search and sort, while `Quick Filters`
owns the immediate status/section narrowing path plus its local reset action.
Those badge groups now wrap inside the native window as well, so narrower app widths no longer
force the operator to horizontally pan through active filters or top status chips.
Capture / evaluate / approve / reject / revise / copy actions now report through one shared feedback
banner, and mutation sheets stay open on failure so the operator can retry without re-entering input.
The evaluate sheet uses a meaning-bearing pull-down (`Quick check` / `Local AI check` / `External AI check`)
instead of numeric-only level selection, and the same short labels appear in queue/detail summaries.
Queue detail also keeps a candidate-specific result strip for the currently selected candidate when
the latest action affected that candidate.
The same Queue detail area now groups readiness badges, review actions, and shortcut hints into one
review command deck so the operator can decide and act without scanning multiple boxes.
Queue detail now also exposes direct copy actions for candidate detail, diff, and lineage so the
current review context can be moved into notes or chats without manual selection.
Home also promotes the first review target, first quick link, and first daemon action into one
start-here section so the initial path is obvious after launch.
Daemon now mirrors that with a focus section that promotes the first next-action item, the current
LaunchAgent status, and the runbook entry point before the longer diagnostic sections.
The same native daemon screen now also adds an `Operator Summary Rail` directly underneath so the
current gate, next command, and next read surface stay visible together before the longer operator
workspace.
The `Start Here` cards above it now work as direct navigation entries, so the operator can jump to
the matching daemon section instead of treating those cards as read-only summaries.
The section navigator now follows that same ordering and splits `Priority Sections` from the
remaining sections, so the upper daemon navigation stays aligned with the current operator path.
The next-epic workspace below now keeps only the remaining workstreams that are not already covered
by that upper priority path, reducing repeated packaging / recovery / supervision summaries.
The deeper review blocks below it now also follow that same priority path order, so gate review,
decision assist, evidence drill-down, and remaining workstreams read in one consistent sequence.
The LaunchAgent section now also keeps one compact `LaunchAgent Focus` summary first, while the
lower detail groups focus on verification evidence and diagnostic breakdowns instead of repeating
that same top-line summary.
Those lower LaunchAgent detail groups now also copy their current state and recovery preview text
directly to the clipboard for handoff and troubleshooting.
The operator summary rail, phase-closure gate guide, suggested-action block, and evidence drill-down
now also expose direct copy actions, so daemon-side handoff text can be taken out without manually
rebuilding the current operator context.
The daemon header now also exports one combined handoff note as plain text, bundling operator summary,
phase gates, suggested actions, read surfaces, and LaunchAgent state into a single save action.
That exported note now also records generation time, profile, Bridge URL, health endpoint, and the
current Bridge status detail so the saved artifact doubles as a minimal operator evidence snapshot.
The exported filename is now timestamped, and the note also includes Bridge version plus source-updated
metadata when available, so repeated handoff saves stay distinct and easier to audit later.
It now also includes component identity plus the local token/log file paths, making the exported note
usable as a first-pass reconnect and log-triage artifact on its own.
The same top block now also includes the compatibility-shell entry URL and the first next-command summary, so
handoff/debug artifacts still preserve both the browser compatibility check and the initial daemon action. When the
local token file is available, that entry prefers the bootstrap URL automatically.
It now also includes `launchctl print` plus stdout/stderr tail commands when available, so the saved
note can hand off the first CLI inspection steps without requiring another pass through the app UI.
The exported note now also carries the main preflight and proof-diagnostics entry commands, so the
same artifact can anchor both readiness verification and deeper proof-oriented diagnosis.
Those command groups are now sectioned more clearly, so status inspection, log-follow, preflight,
and proof entry paths can be scanned quickly during handoff.
The later operator-summary and LaunchAgent blocks now follow the same section-header pattern, so the
entire exported note reads more like a compact handoff document than a raw clipboard dump.
Those later blocks are now also ordered to match the operator flow more closely, moving from summary
and next action into gates, read surfaces, and finally LaunchAgent state and recovery detail.
The opening metadata now also sits under an explicit Bridge Context header, making the full note read
as one consistent handoff template from environment through action and diagnosis.
That opening header is now sourced from `AppStrings`, so the handoff note follows the same i18n path
as the rest of the native app instead of relying on a hard-coded English label.
The same pass now also localizes more diagnostic labels in Japanese mode, reducing mixed-language
handoff output around bridge metadata and diagnostic sections.
The CLI-adjacent labels in that note now also come from `AppStrings`, including the component label
and the log-follow section heading, which keeps later handoff wording adjustments centralized.
The LaunchAgent Runbook now follows that same flow by showing preflight, verification, and proof
diagnostics before logs and lower-level preview details.
The LaunchAgent command deck now also follows that macOS flow by placing inspect first, then
recover, then start, and finally log actions.
Its inspect group now keeps only non-mutating status and health checks, while the recover group
surfaces cleanup, repair, and then bootout before restart commands.
Each group now also carries a short summary so the operator can understand the intent before reading
the commands themselves.
The section now also starts with one compact `LaunchAgent Focus` block so current state, recovery
preview, and the next suggested command can be scanned before the lower `Current State Details`
and `Recovery Preview Details` verification groups.

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
- supported startup command, debug compatibility URL, and phase-closure checklist visibility
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

The Bridge-hosted compatibility shell still uses:

```text
GET /app/ui?bootstrap_token=...
```

and then continues with the dedicated resident app UI session cookie.
