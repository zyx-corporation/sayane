# Phase 6: Semantic Review Layer — Evaluation Record

## Status: closed_with_notes

**Date**: 2026-06-05

## Principle

```
言葉を保存するだけでは足りない。
意味の置き場所を監査する。
```

## Implementation

| Component | Status |
|---|---|
| `semantic_review.py` | ✅ |
| Known Concept Hint Registry | ✅ 6 concepts |
| Token extraction + normalization | ✅ |
| Duplicate concept detection | ✅ |
| Semantic placement analysis | ✅ |
| Identity boundary check | ✅ |
| CLI output update | ✅ |
| T-RDE tests | ✅ 6 tests |

## Candidate Count Investigation

| Phase | Bundle | Count | Reason |
|---|---|---|---|
| Phase 5 observed | A2 ChatGPT return (`a2-chatgpt-return.yml`) | 5 | Bundle has interaction, writing, technical, principles, important_terms — all match `_IMPORTABLE_SECTIONS` |
| Phase 6 observed | A2b Claude return (`a2b-claude-return.yml`) | **2** | Claude renamed sections to `interaction_style`, `response_policy` — only `technical` and `principles` match importable sections |
| Semantic Review Layer | Any | **0** | Review pass adds metadata only — never creates/modifies/deletes candidates |

```yaml
candidate_count_note:
  phase5_observed: 5  # A2 ChatGPT bundle (more importable sections)
  phase6_observed: 2  # A2b Claude bundle (renamed sections: interaction_style, response_policy)
  reason: "Claude renamed interaction→interaction_style, writing→response_policy. These names are not in _IMPORTABLE_SECTIONS, so only technical and principles generate candidates."
  semantic_review_layer_mutates_candidates: false
```

## Sayane Overlap Behavior

Both `rde` and `sayane` are detected across candidates:

```
Overlaps:
  terms=['rde'] candidates=[0, 1]
  terms=['sayane'] candidates=[0, 1]
```

Candidate 1 (technical) receives both placement warnings:
- `RDE may be flattened if imported as a generic technical preference.`
- `Sayane may be flattened if imported as a generic technical preference.`

## Warning Messages

| Context | Message |
|---|---|
| Known concept in discouraged section | `{term} may be flattened if imported as a generic {section} preference.` |
| Identity boundary violation | `'{term}' should not be placed in {section}.` |
| Duplicate concept overlap | `Same concept '{term}' appears in multiple sections. Review canonical placement before approval.` |

## RDE Assessment

### Preserved
- Candidate gate (import creates Candidates, not direct mutations)
- No auto-approve
- No auto-reject
- Hint-only registry
- Candidate non-mutation

### Transformed
- Import output now contains review metadata
- CLI surfaces semantic warnings

### Supplemented
- Semantic overlap detection
- Unstable placement detection
- Boundary sensitive detection
- T-RDE regression tests

### Unresolved
- `interaction_style`, `response_policy` not in `_IMPORTABLE_SECTIONS` (design choice — Claude renamed sections)
- Candidate count difference between A2 and A2b documented

### Critical Distortion
- **None**

## Test Results

```yaml
tests:
  total: 37
  passed: 37
  semantic_review: 6
  import_bundle: 5
  import_hygiene: 8
  export: 7
  export_golden: 5
  export_chatgpt: 6
```

## Confirmed Design Principles

| Principle | Status |
|---|---|
| `auto_approve: false` | ✅ |
| `auto_reject: false` | ✅ |
| `known_concept_registry_authority: hint_only` | ✅ |
| `candidate_non_mutation` | ✅ |
| `semantic_review_layer adds metadata only` | ✅ |

## Regression Expectation (A2b)

```yaml
a2b_semantic_review_expected:
  import_success: true
  candidates_count: 2
  semantic_review_layer_mutates_candidates: false
  candidate_1:
    section: technical
    flags:
      - review_required
      - unstable_placement
      - semantic_overlap
    warnings:
      - term: RDE
      - term: Sayane
  candidate_2:
    section: principles
    flags:
      - semantic_overlap
      - review_required
  overlap_warnings:
    - terms: [rde]
      candidates: [0, 1]
    - terms: [sayane]
      candidates: [0, 1]
```

## Remaining Notes

1. Claude renamed `interaction` → `interaction_style`, `writing` → `response_policy`. These are not in `_IMPORTABLE_SECTIONS`, so only `technical` and `principles` generate candidates.
2. Future Phase 7+: consider section name normalization or alias mapping in import.

## Next Phase Recommendations

```yaml
phase7_candidates:
  - Candidate Review UI warning badge refinement
  - approve / reject / modify workflow hardening
  - lineage event logging for semantic warnings
  - import decision audit trail
  - regression dashboard for cross-LLM transfer tests
```
