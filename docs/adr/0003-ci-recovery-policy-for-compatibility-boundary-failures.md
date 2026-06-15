# ADR 0003: CI Recovery Policy for Compatibility-Boundary Failures

## Status

Accepted

## Context

During the CI recovery for issue #402, the failing tests were not caused by a single implementation bug. The failures appeared across several compatibility boundaries at the same time:

- CLI compatibility versus safe backend/API defaults.
- Profile-initialized assumptions versus capture candidate creation before profile initialization.
- Legacy Candidate JSON versus the current `CandidateUpdate` schema.
- Refined ChatGPT export versus older CLI and golden-test expectations.
- Complete YAML documents versus clipboard fragments that only contain a partial YAML section.
- Package-qualified `tests.*` imports versus pytest-style test module discovery.
- Fixed fixture slices versus assertions that referenced values outside the sliced range.

This made the recovery different from a normal red-green fix. A change that satisfied one test could re-open another compatibility edge. The work therefore required separating implementation regressions from test expectation drift, and preserving user-facing compatibility without weakening storage and safety defaults.

## Decision

When recovering CI failures that cross compatibility boundaries, Sayane will use the following policy.

1. Classify each failure before changing code.
   - If the failure exposes a real product behavior regression, fix the implementation.
   - If the failure is caused by stale fixtures or assertions, fix the fixture or test expectation.
   - If both are involved, fix the implementation first and then align the test.

2. Preserve backend/API safety defaults.
   - Backend and API paths must not implicitly create Git commits merely because a local profile happens to be filesystem-backed.
   - CLI compatibility may be preserved through explicit compatibility paths, not through broad default behavior.

3. Keep legacy compatibility narrow and named.
   - Legacy Candidate JSON may be upgraded at read time.
   - Legacy CLI auto-commit behavior may be preserved only for explicit CLI-compatible actions or explicit opt-in.
   - Legacy paths should have clear tests and comments so they do not become new implicit defaults.

4. Treat partial clipboard YAML as a supported input shape.
   - A clipboard fragment containing an `important_terms:` block may be classified as `important_terms` even if the fragment is not a complete YAML document.
   - Full YAML parse failure should not automatically override a more specific, safely recoverable fragment classification.

5. Treat export golden files as part of the public contract.
   - Refined ChatGPT export sections such as `Philosophical Stance`, `Principles`, `Execution Context`, and `Export Policy Notes` are specification-bearing output.
   - If a compatibility line such as `Identity:` is intentionally restored, golden fixtures must be updated at the same time.

6. Keep fixture-slice tests honest.
   - Tests based on fixed line slices must assert values that are actually inside that slice.
   - Such tests should verify the semantic purpose of the test, for example preserving exact raw capture content, rather than depending on a value located outside the slice.

7. Stop code changes once CI is green.
   - After CI success, additional work should be documentation, ADRs, or issue notes unless a new concrete failure appears.
   - Green CI marks the end of the recovery loop, not the start of speculative cleanup.

## Consequences

This policy makes CI recovery slower than directly patching the first visible failure, but it reduces the risk of oscillating fixes. It also keeps compatibility work from silently broadening unsafe defaults.

The trade-off is that some legacy paths remain in the codebase. This is acceptable only when the path is explicit, bounded, and covered by tests.

## Applied Example: #402

The #402 recovery applied this policy across the following areas:

- Ruff, formatting, and workflow YAML recovery.
- Storage backend Git auto-commit compatibility.
- Capture and lineage behavior before profile initialization.
- Legacy Candidate JSON preview compatibility.
- Restoration of the `xxx.yaml` important-terms fixture.
- Acceptance coverage import resolution after making `tests/` importable.
- Source timestamp offset preservation in build info display.
- `important_terms` YAML fragment inference for clipboard captures.
- Restoration of refined ChatGPT export sections.
- Golden fixture alignment for current ChatGPT markdown export.
- Clipboard `raw_capture` regression expectation alignment with the actual fixed sample fragment.

The final recovery result was CI success on `main` at commit `1b97e8e`.
