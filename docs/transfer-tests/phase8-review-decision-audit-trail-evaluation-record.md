# Phase 8: Review Decision Audit Trail — Evaluation Record

## Status: closed_with_notes

**Date**: 2026-06-05

## Principle

```
判断は消えてはいけない。
採用された言葉だけでなく、棄却された候補にも来歴がある。
```

## Implementation

| Component | Status |
|---|---|
| Audit record schema | ✅ `build_audit_record()` |
| Append-only JSONL store | ✅ `AuditStore` |
| Decision diff representation | ✅ `delta_summary` |
| Audit CLI | ✅ `sayane audit list/by-candidate/by-term` |
| Review → audit integration | ✅ auto-append on review decision |
| Query by candidate/term/decision_type | ✅ |
| A2b audit fixtures | ✅ |
| T-RDE tests | ✅ 10 tests |

## Safety Constraints

| Constraint | Status |
|---|---|
| No decision without audit record | ✅ audit append before profile update |
| Rejected candidates preserved | ✅ original_candidate in audit |
| Modified candidates preserve original | ✅ diff shows both original and applied |
| Semantic warnings preserved | ✅ in audit record |
| Append-only (no modification) | ✅ |
| Readable without database | ✅ JSONL |

## Audit CLI

```bash
sayane audit list                        # Last 20 records
sayane audit by-candidate c-reject      # All decisions for a candidate
sayane audit by-term RDE                # Records referencing RDE
```

## Test Results

```yaml
tests:
  total: 383
  passed: 383
  phase8_tests: 10
  phase7_tests: 12
  phase8_regressions: 0
```

## RDE Assessment

### Preserved
- Original candidate value
- Decision reason
- Semantic warnings at decision time
- Rejected candidates
- Modified candidate delta

### Transformed
- Review decision → audit record

### Supplemented
- Queryable audit trail
- Append-only store
- Delta summary
- Transfer path lineage

### Unresolved
- In-memory ↔ file persistence for Phase 7 review decisions (store is in-memory; audit is file-backed)

### Critical Distortion
- **None**

## Next Phase Recommendations

```yaml
phase9_candidates:
  - Context Bundle Signing / Provenance Verification
  - Cross-LLM Transfer Regression Dashboard
  - Import Policy Profiles
  - Candidate Review UI Polishing
```
