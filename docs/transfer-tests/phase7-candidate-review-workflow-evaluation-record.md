# Phase 7: Candidate Review Workflow Hardening — Evaluation Record

## Status: closed_with_notes

**Date**: 2026-06-05

## Principle

```
検出された意味の揺れを、人間がどう引き受け、どう記録するか。
```

## Implementation

| Component | Status |
|---|---|
| Review Decision Model | ✅ `review_decision.py` |
| Lineage event schema | ✅ `build_lineage_event()` |
| approve / reject / modify / defer | ✅ |
| Validation (reason required, applied_value required) | ✅ |
| Overlap group resolution | ✅ |
| CLI review commands | ✅ `sayane review list/approve/reject/modify/defer` |
| A2b review fixture | ✅ |
| T-RDE tests | ✅ 12 tests |

## Design Constraints

| Constraint | Status |
|---|---|
| No auto-approve | ✅ |
| No auto-reject | ✅ |
| review_required approve requires reason | ✅ |
| Modify preserves original candidate | ✅ |
| Reject records lineage event | ✅ |
| Defer keeps candidate pending | ✅ |
| All decisions produce lineage events | ✅ |

## A2b Recommended Decisions

```yaml
candidate_1 (technical):
  decision: reject
  reason: "RDE and Sayane should not be flattened into generic technical preferences."

candidate_2 (principles):
  decision: modify
  applied_value:
    principles:
      - RDE
      - Context portability via Sayane
  reason: "RDE belongs to principles; Sayane should be represented as a context portability basis."
```

## CLI Usage

```bash
# List decisions
sayane review list

# Reject a candidate
sayane review reject candidate-001 \
  --reason "RDE and Sayane should not be flattened into generic technical preferences."

# Modify and approve
sayane review modify candidate-002 \
  --value '{"principles": ["RDE", "Context portability via Sayane"]}' \
  --reason "RDE belongs to principles; Sayane represented as context portability basis."

# Defer
sayane review defer candidate-003 --reason "Need more context."

# Approve (reason required if review_required)
sayane review approve candidate-004 --reason "Verified: correct placement."
```

## RDE Assessment

### Preserved
- Candidate gate (no direct profile mutation)
- Semantic review metadata
- Original candidate value
- Human decision boundary

### Transformed
- Candidate warnings → review decision
- Review decision → lineage event

### Supplemented
- Decision reason (human documentation)
- Applied value for modify
- Overlap group resolution
- Transfer path lineage

### Unresolved
- In-memory decision store (persistence to file storage is follow-up)

### Critical Distortion
- **None**

## Test Results

```yaml
tests:
  total: 373
  passed: 373
  phase7_tests: 12
  phase7_regressions: 0
```

## Next Phase Recommendations

```yaml
phase8_candidates:
  - Review Decision Audit Trail (persist decisions to disk)
  - Cross-LLM Transfer Regression Dashboard
  - Candidate Review UI polishing
  - Import Policy Profiles
  - Context Bundle Signing / Provenance
```
