# Context Portability A1: ChatGPT Baseline Report

## Status

**Baseline usable.** ChatGPT target export is confirmed to preserve context meaning across the Sayane → ChatGPT transfer boundary.

## Test Metadata

- **Test ID**: A1
- **Date**: 2026-06-05
- **Source**: Sayane external profile (`examples/profiles/minimal.yaml`)
- **Target**: ChatGPT
- **Export format**: markdown
- **Target adapter**: chatgpt (compact, refined per #153)
- **Adapter version**: Post-#153, Post-#155

### Scopes

- `identity`
- `interaction`
- `writing`
- `technical`
- `ethics` (included in retest)

## Export Command

```bash
sayane export \
  --format markdown \
  --scope identity,interaction,writing,technical \
  --target chatgpt \
  --profile examples/profiles/minimal.yaml
```

## External Profile Boundary

The receiving ChatGPT session recognized the exported content as **session-scoped external context**, not persistent model memory. It correctly treated the profile as a portable response-policy packet rather than a personality copy or "memory."

Key boundary signals in the export:

```markdown
## Metadata
- Source: Sayane external profile
- LLM memory: false

## How to Use This Context
This profile is external context supplied by Sayane.
It is not ChatGPT memory.
Use it to guide responses within this session...
```

## Fixed Tasks

The following tasks were used in the A1 retest:

### Task 1: Response Style Policy Summary

> Summarize the response style policy embedded in this context.

**Expected**: Identify tone (precise, logical, explicit uncertainty), language (ja), collaboration style (structured reasoning).

### Task 2: Technical Design Constraints

> Describe what a technical design answer should preserve according to this context.

**Expected**: Reference local-first architecture, auditability, Context Portability, RDE principles.

### Task 3: Public-Facing Profile

> Create a public-facing profile description without private or formation-layer details.

**Expected**: Extract identity roles, projects, concepts — omit internal policy, private fields.

### Task 4: Sayane Explanation (ja)

> Sayaneを800文字以内の日本語で説明してください。

**Expected**: Japanese response explaining Sayane as a context portability tool with audit, lineage, and external profile boundaries.

## Observed Result

ChatGPT correctly:

- Recognized the profile as session-scoped external context
- Used Japanese by default
- Applied precise, logical tone with explicit uncertainty
- Referenced local-first design, auditability, Context Portability
- Distinguished Kotone as a system that produces ΔM with RDE audit
- Noted remaining duplication/noise (addressed by #155)

## RDE Evaluation

### Preserved Elements

- External profile boundary (not LLM memory)
- Japanese response preference
- Constructive critique preference
- Technical design constraints (local-first, auditability, Context Portability)
- RDE / Kotone / Sayane semantic relationship

### Authorized Transformations

- ChatGPT reframed the bundle as "session-scoped external context"
- ChatGPT described the profile as a "portable response-policy packet" rather than a personality copy
- These are acceptable reformulations within the target LLM's expression style

### Inferred Extensions

- "Kotone produces ΔM and audits it through RDE"
  - **Marked as interpretive.** Not yet canonicalized through Candidate Review.
  - Useful as a transfer quality signal, not as source of truth.

### Unresolved Gaps

- Remaining source hygiene concerns addressed by #155 (noise filtering layer)
- Future LLM targets (Claude, Gemini, DeepSeek) may preserve different context elements
- Multi-target consistency not yet measured

### Suspicious Drift

- ChatGPT may decide on its own what is "noise" unless Sayane provides structured noise classification
- Mitigation: #155 source hygiene layer removes noise before export
- Remaining risk: target LLM may re-interpret ambiguous context

### Critical Distortion

- **None observed.**

## Adapter Improvement History

| PR/Issue | Date | Change |
|---|---|---|
| #141 | 2026-06-05 | Initial export: yaml, markdown, prompt with scope filtering |
| #146 | 2026-06-05 | ChatGPT compact adapter (first version) |
| #153 | 2026-06-05 | Refined structure: metadata, quote/interpretation, principles, execution_context |
| #155 | 2026-06-05 | Source hygiene: UI/session noise filtering + deduplication |

## Remaining Risks

1. **Multi-target consistency**: Only ChatGPT tested. Claude/Gemini/DeepSeek may respond differently.
2. **Interpretive drift**: ChatGPT reformulated Kotone/RDE in its own terms. Acceptable for transfer, but not canonical.
3. **Source profile quality**: Garbage in = garbage out. Profile hygiene affects all exports.

## Readiness Judgment

**ChatGPT target export is baseline-usable.**

The exported context:
- Preserves meaning across the transfer boundary
- Is recognized as external context, not LLM memory
- Respects export policy (no `promptExport: never` fields)
- Has no critical distortions

### Proceed to:

1. ✅ A1 baseline documented (this report)
2. → #143: Import-to-Candidate Review flow
3. → Claude / Gemini / DeepSeek baseline tests (follow A1 template)
4. → A2 round-trip test (ChatGPT ↔ Claude)

## Related

- `docs/transfer-test-protocol.md` — Full test protocol
- `docs/transfer-tests/a1-bundle.md` — Export fixture
- `docs/transfer-tests/a1-chatgpt-baseline.md` — First procedure
- `docs/transfer-tests/a1-chatgpt-retest.md` — Post-#153 retest
- `docs/transfer-tests/template.md` — RDE report template
- `docs/adr/0001-context-portability-export-import.md`
- Issue #142, #143, #153, #155
