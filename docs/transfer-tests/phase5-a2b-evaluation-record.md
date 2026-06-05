# Phase 5 A2b Evaluation Record

Created: 2026-06-05T18:09:19+09:00
Status: usable_with_notes

## Test Target

A2b: ChatGPT → Claude → Sayane Import

Flow:

```text
Sayane → export → ChatGPT → return bundle → Claude → return bundle → Sayane import
```

## Command

```bash
sayane import-bundle docs/transfer-tests/a2b-claude-return.yml --profile examples/profiles/minimal.yaml
```

## Observed Result

```text
2 件の候補が見つかりました:

--- Candidate 1 ---
  Section: technical
  Action:  add
  Proposed: {"preferences": ["RDE", "Sayane"]}

--- Candidate 2 ---
  Section: principles
  Action:  add
  Proposed: ["RDE", "Sayane"]
```

## Evaluation Summary

A2b import succeeded.

The Claude return bundle was accepted by `sayane import-bundle` and converted into review candidates rather than being directly written into the target profile. This confirms that the candidate gate worked as intended.

No critical distortion was observed.

However, two related candidates were produced:

- `RDE` and `Sayane` appeared under `technical.preferences`
- The same terms also appeared under `principles`

This indicates semantic overlap and unstable semantic placement. The terms were preserved lexically, but their canonical role became ambiguous.

## Candidate Review Recommendation

### Candidate 1

```yaml
section: technical
action: add
proposed:
  preferences:
    - RDE
    - Sayane
```

Recommended decision: reject or modify.

Reason:

`RDE` is not merely a technical preference. It is an evaluation and audit principle for meaning-change and drift.

`Sayane` is not merely a technical preference. It is a context portability and candidate-review system.

Placing both terms as generic technical preferences risks flattening their meaning.

### Candidate 2

```yaml
section: principles
action: add
proposed:
  - RDE
  - Sayane
```

Recommended decision: modify_then_approve.

Preferred normalized form:

```yaml
principles:
  - RDE
  - Context portability via Sayane
```

Reason:

`RDE` belongs more naturally to principles, evaluation policy, or audit methodology.

`Sayane` should be represented as a context portability basis, not merely as a name or generic preference.

## RDE Assessment

```yaml
phase5_a2b_rde_assessment:
  preserved:
    - external_profile_boundary
    - assistant_identity_boundary
    - candidate_gate
    - RDE
    - Sayane
  transformed:
    - ChatGPT_return_bundle_was_reencoded_by_Claude
    - Claude_return_bundle_was_converted_into_Sayane_candidates
  supplemented:
    - RDE_and_Sayane_were_classified_into_import_sections
  unresolved:
    - canonical_section_for_RDE
    - canonical_section_for_Sayane
    - duplicate_concept_handling
  suspicious_drift:
    - RDE_as_technical_preference
    - Sayane_as_generic_preference
    - duplicate_registration_across_sections
  critical_distortion:
    - none
  judgement: usable_with_notes
  next_update:
    - add_semantic_overlap_warning
    - add_semantic_placement_review
    - add_phase5_a2b_regression_fixture
```

## Phase 5 Status Update

```yaml
phase5_status:
  A1_ChatGPT_baseline: usable
  A2_ChatGPT_round_trip: completed
  Claude_baseline: usable
  A2b_ChatGPT_to_Claude_import: usable_with_notes
```

## Follow-up Requirement for Phase 6

Phase 6 should add a semantic review layer to Sayane import.

Required additions:

1. Semantic overlap detection
2. Semantic placement review
3. Known concept hint registry
4. CLI warning output
5. Candidate review UI warning badges
6. A2b regression fixture
7. T-RDE tests for:
   - RDE placement
   - Sayane placement
   - external profile boundary
   - assistant identity boundary
   - hint-only concept registry behavior

## Design Conclusion

A2b should be considered successful with notes.

The test demonstrated that cross-LLM context transfer can preserve important terms, but also that lexical preservation alone is insufficient.

A term can survive while its semantic placement drifts.

Therefore, Sayane should not be treated as a simple memory or profile import tool. It should function as a candidate and lineage system that helps humans review whether imported context is semantically safe to accept.
