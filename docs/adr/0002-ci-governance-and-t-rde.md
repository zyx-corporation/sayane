# ADR 0002: CI Governance and T-RDE Execution Surface

## Status

Proposed

## Context

Sayane is no longer a CLI-only toolkit. It includes CLI, Local Bridge, MCP, storage security policy, Candidate Review, a future resident app service, Local Vault, and UI surfaces.

This makes CI more than a test runner. CI defines which design boundaries are continuously checked and which changes are allowed to close a phase or issue.

Because Sayane uses T-RDE-oriented development, CI is one execution surface for detecting implementation drift from the intended design.

## Decision

CI is a project-wide governance mechanism.

Core CI is the primary phase gate. Observation / E2E checks are separate surface gates. CI pass is required evidence for closing implementation issues, but CI pass is not correctness certification.

CI workflow changes must be treated as architecture governance changes.

## Principles

### 1. CI is project-wide

CI applies to the whole Sayane project, not only the touched component.

Local changes can violate cross-cutting boundaries such as:

- Candidate review boundary
- MCP exposure boundary
- storage security boundary
- Local Vault unlock boundary
- Extension freeze boundary
- app clipboard capture boundary

Relevant project-wide checks must remain active even when a change appears local.

### 2. Core CI is the primary phase gate

Core CI is the primary gate for phase progress.

A phase or issue must not be considered complete when Core CI fails.

Core CI includes:

- Python lint / format checks
- unit tests
- targeted storage/security checks
- MCP context exposure checks
- future Local Vault key/unlock tests

### 3. Observation / E2E is a separate surface gate

Observation / E2E checks verify runtime or UI-facing behavior. They are not substitutes for Core CI.

Examples:

- Extension E2E
- App clipboard capture smoke test
- MCP client integration smoke test
- UI review queue smoke test
- packaging / installer smoke test

Observation / E2E may block release or surface completion, but it does not replace Core CI.

### 4. Issue closure requires CI evidence

Before closing an implementation issue, the closing comment or PR summary should record:

- relevant commit(s)
- CI workflow or local command executed
- pass / fail result
- unresolved warnings
- warning classification
- remaining follow-up issues, if any

Issue closure is not merely “code was written”; it is “code was written and bounded verification evidence was recorded.”

### 5. Warnings must be classified

Warnings must be classified into one of three categories:

| Category | Meaning | Effect |
| --- | --- | --- |
| blocking | Must be resolved before phase/issue closure | Blocks close / merge |
| tracked separately | Does not block this issue, but requires a follow-up issue | Link follow-up |
| informational | Recorded for context only | Does not block |

Unclassified warnings must not be silently ignored.

### 6. CI workflow changes are architecture governance

Changing CI changes what the project treats as enforceable truth.

Therefore CI workflow changes must be reviewed as architecture governance, not as incidental maintenance.

Examples of governance-impacting CI changes:

- removing targeted security checks
- weakening MCP exposure checks
- dropping Local Vault tests
- changing Extension freeze checks
- changing phase gate rules
- turning blocking checks into non-blocking checks

### 7. CI is a T-RDE execution surface

T-RDE checks whether implementation preserves, transforms, supplements, or deviates from the intended design.

CI operationalizes part of T-RDE by making selected boundaries executable.

Examples:

- storage tests preserve the “local-first is not plaintext-local” boundary
- MCP tests preserve the “pending/rejected Candidate must not become normal context” boundary
- unlock tests will preserve the “UI unlock is not MCP access” boundary
- Extension freeze checks preserve the “browser automation is not the core Sayane value” boundary

### 8. CI pass is not correctness certification

CI pass means only that known checks passed in a bounded environment.

CI pass does not prove:

- semantic correctness
- absence of vulnerabilities
- absence of privacy risk
- conceptual alignment with all design goals
- correctness of unknown cases

CI pass is bounded evidence, not certification.

## Required CI structure

### Core CI

Core CI should include:

- lint
- format
- unit tests
- targeted architecture/security tests
- MCP exposure tests
- storage boundary tests
- future Local Vault key/unlock tests

Current minimum targeted checks:

```bash
pytest -v tests/test_storage_backend.py
pytest -v tests/test_storage_security_policy.py
pytest -v tests/test_storage_write_policy.py
pytest -v tests/test_mcp_context.py
```

### Surface CI / Observation E2E

Surface CI should be separated from Core CI.

Examples:

```bash
# Extension freeze period only
cd extension
npm ci
npm run typecheck
npm run build
```

Future examples:

```bash
pytest -v tests/test_app_clipboard_capture.py
pytest -v tests/test_mcp_client_smoke.py
pytest -v tests/test_review_queue_ui_smoke.py
```

## Issue close template

Recommended close note:

```markdown
## Verification

Commits:

- `<sha>` — summary

CI / checks:

- Core CI: pass / fail
- Targeted checks: pass / fail
- Observation E2E: pass / fail / not applicable

Warnings:

- blocking: none / list
- tracked separately: #...
- informational: ...

RDE note:

- preserved:
- transformed:
- supplemented:
- unresolved:
```

## Consequences

Benefits:

- Phase completion becomes auditable.
- CI changes become explicit governance events.
- T-RDE principles are connected to executable checks.
- Security boundaries are less likely to be weakened accidentally.
- Issue closure carries verification evidence.

Costs:

- More CI maintenance.
- More explicit issue/PR discipline.
- Some changes may require updating CI before implementation can proceed.
- CI pass must still be interpreted carefully and cannot replace review.

## Non-goals

This ADR does not claim that CI proves correctness.

This ADR does not define all future test suites.

This ADR does not require every warning to block progress.

This ADR does not replace human review, RDE review, security review, or threat modeling.

## Follow-up work

- Update `docs/ci.md` to reference this ADR.
- Add issue close checklist to PR / issue templates.
- Ensure Core CI remains the primary phase gate.
- Define Observation E2E gates for app clipboard capture and UI review queue.
- Add future Local Vault tests once `PlatformKeychainProvider`, `KeyManager`, and unlock sessions exist.

## RDE audit note

This ADR preserves the distinction between evidence and proof.

CI is a practical execution surface for T-RDE, but it only covers explicit checks. It can detect known forms of design drift, but it cannot certify that the system is correct, safe, or semantically complete.

The strongest claim CI may make is: “the current implementation passed the current bounded checks.”
