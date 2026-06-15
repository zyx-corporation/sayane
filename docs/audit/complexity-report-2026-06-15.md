# ADR 0004 Complexity Report: 2026-06-15

## Status

This document records the first stored complexity-report capture for ADR 0004 and #177.

The report remains informational only. It does not introduce a CI hard gate, does not fail builds, and does not authorize behavior changes.

## Intended Command

```bash
python scripts/complexity_report.py src tests
```

The local execution environment available to this capture could not clone or run the repository checkout. Therefore, this file records the report command, script behavior, reviewed baseline targets, and gate policy. A future developer workstation or CI artifact should replace or supplement this file with the exact stdout from the command above.

## Script Behavior

The complexity reporter is dependency-free and uses only the Python standard library. It scans Python files under the provided paths and reports warning candidates for:

- file length
- god-file names
- function length
- class length
- approximate cyclomatic complexity
- parse errors

The script is explicitly informational. It must not be used as a hard CI gate until baseline exceptions and thresholds are reviewed.

## Warning Thresholds

The current script-level thresholds are:

```text
FILE_WARN_LINES = 300
FILE_HIGH_LINES = 500
FUNCTION_WARN_LINES = 50
CLASS_WARN_LINES = 200
CYCLOMATIC_WARN = 10
CYCLOMATIC_HIGH = 20
```

Current god-file name candidates are:

```text
app.py
main.py
service.py
manager.py
utils.py
common.py
helper.py
```

These values are review triggers, not automatic failure criteria.

## Current Baseline Targets

The current manual ADR 0004 baseline identifies the following responsibility-boundary risks.

### High priority

- `src/sayane/cli/app.py`
  - CLI god-file candidate
  - `app.py` warning name
  - multiple command groups in one module
  - tracked by #172

- `src/sayane/bridge/app.py`
  - FastAPI app factory and route implementation mixed in one module
  - `app.py` warning name
  - tracked by #173

### Medium priority

- `src/sayane/evaluators/capture_parse.py`
  - YAML detection, syntax error handling, persona classification, important-terms classification, and fragment extraction mixed in one module
  - tracked by #174

- `src/sayane/core/export.py`
  - scope selection, noise filtering, YAML/prompt/markdown rendering mixed in one module
  - golden-test-backed output makes it contract-sensitive
  - tracked by #175

- `src/sayane/bridge/candidate_api.py`
  - API presentation, lifecycle checks, approval policy, revision, lineage, and UI preview mixed in one module
  - tracked by #176

## Recommended Execution Order

1. #177 Add complexity reporting baseline for ADR 0004
2. #172 Refactor CLI app into command group modules
3. #173 Refactor Bridge app into route modules
4. #174 Refactor capture parser into detection and classifier modules
5. #175 Refactor export module into scoped renderer modules
6. #176 Refactor candidate API into lifecycle, policy, and presenter modules

## Gate Policy

Do not enable a hard CI gate yet.

Before CI enforcement, review:

- whether generated counts match the manual baseline
- whether current large modules need temporary baseline exceptions
- whether thresholds should distinguish `src` and `tests`
- whether `scripts/complexity_report.py` should become an informational CI artifact first
- whether an external tool such as `radon` should be compared without becoming mandatory

## Non-Goals

This report does not authorize changes to:

- CLI command names
- CLI output text
- Bridge endpoint URLs
- Bridge response payload shape
- export golden fixtures
- ChatGPT refined export output
- candidate lifecycle semantics
- RDE approval policy
- Git auto-commit policy

## Next Step

Proceed to #172 as a mechanical CLI command-group split. Keep behavioral delta minimal: move registration code by command group, preserve public command names and output text, and rely on existing tests/golden fixtures to detect unintended meaning drift.
