# Complexity Baseline: 2026-06-15

## Purpose

This baseline supports ADR 0004: Python Code Size and Complexity Management Criteria.

It is informational only. It must not fail CI by itself. The goal is to make current complexity and responsibility-boundary risks visible before structural refactoring begins.

Related issues:

- Parent tracking issue: #171
- Complexity reporting baseline: #177
- CLI command group split: #172
- Bridge route split: #173
- Capture parser split: #174
- Export renderer split: #175
- Candidate lifecycle / policy / presenter split: #176

## Baseline Method

This first baseline is based on manual code review performed during the ADR 0004 audit. It does not yet include automated `radon` output.

Future updates may add:

- line-count report
- function-length report
- class-length report
- cyclomatic complexity report
- god-file name scan
- informational CI artifact

## ADR 0004 Warning Thresholds

ADR 0004 defines the following warning thresholds:

```text
file: 300-500 lines => review split
function: 30-50 lines => review split
class: 200 lines => review split
function arguments: >5 => consider dataclass / command object
nesting: >3 => consider early return or function split
cyclomatic complexity: >10 review, >20 refactor by default
```

These are warning values, not hard prohibitions.

## Current Manual Findings

### High priority

#### `src/sayane/cli/app.py`

Risk type:

- god-file candidate
- `app.py` warning name
- multiple command groups in one module
- CLI, filesystem, environment, YAML settings, profile initialization, capture, export, review, storage, and MCP responsibilities in one file

Tracking issue:

- #172

Recommended action:

Split into command group modules while preserving CLI behavior.

#### `src/sayane/bridge/app.py`

Risk type:

- `app.py` warning name
- FastAPI app factory and route implementation in one file
- auth dependency, route registration, HTTP exception mapping, profile loading, export/import, candidate, lineage, and context packet endpoints share one module

Tracking issue:

- #173

Recommended action:

Split into FastAPI route modules while keeping `create_app()` as the public factory.

### Medium priority

#### `src/sayane/evaluators/capture_parse.py`

Risk type:

- multiple parser responsibilities
- YAML detection, syntax error handling, persona classification, important-terms classification, fragment extraction, and profile value indexing share one file

Tracking issue:

- #174

Recommended action:

Extract YAML detection, important-terms fragment parsing, important-terms classification, and persona YAML classification.

#### `src/sayane/core/export.py`

Risk type:

- scope selection, noise filtering, YAML export, prompt export, generic markdown export, compact/refined markdown export, and rendering helpers share one file
- export output is golden-test-backed and therefore contract-sensitive

Tracking issue:

- #175

Recommended action:

Split renderers and filtering without changing output or golden fixtures.

#### `src/sayane/bridge/candidate_api.py`

Risk type:

- API presentation, lifecycle transition checks, unsafe approval policy, critical-section confirmation, revision creation, lineage recording, and UI preview generation share one module

Tracking issue:

- #176

Recommended action:

Split presenter, lifecycle usecases, revision usecase, and domain policy.

## Execution Order

Recommended order:

1. #177 Add complexity reporting baseline for ADR 0004
2. #172 Refactor CLI app into command group modules
3. #173 Refactor Bridge app into route modules
4. #174 Refactor capture parser into detection and classifier modules
5. #175 Refactor export module into scoped renderer modules
6. #176 Refactor candidate API into lifecycle, policy, and presenter modules

## Non-Goals

This baseline does not authorize behavior changes.

Do not change:

- CLI command names
- CLI output text
- Bridge endpoint URLs
- Bridge response payload shape
- export golden fixtures
- ChatGPT refined export output
- candidate lifecycle semantics
- RDE approval policy
- Git auto-commit policy

## Next Baseline Update

The next update should add automated measurement, preferably as a local script first.

Candidate next step:

```text
scripts/complexity_report.py
```

The script should report warning candidates but should not fail CI until thresholds and baseline exceptions are reviewed.
