# Phase 3 Closure: Candidate Review / IR / Edit / Removal / Lineage

## Status: Complete

**Date**: 2026-06-05

## Summary

Phase 3 transformed Sayane from a simple Capture + Candidate approval UI into a context editing and semantic audit foundation. All planned capabilities are implemented, tested, and stable.

## Completed Capabilities

### Candidate Review (#119, #120, #138)
- Side panel with filterable candidate list (review_required / all / has_diff / inferred_extension / low_value / debug)
- Classification tooltips on hover (9 review classes)
- Accurate empty state messages (3 differentiated states)
- Judge-failed candidates remain visible
- Already-approved/rejected explicit messaging

### Edited Candidate Creation (#119)
- "Edit and Save" button in expanded card
- Edit view: textarea, section input, reason input
- `POST /candidates/{id}/revise` endpoint
- Lineage preserves original → revised relationship

### Structured Persona IR Import (#124)
- Persona YAML detection with raw blob blocking maintained
- 8 IR sections auto-generated: identity.name, identity.contact, identity.role, organization.profile, interaction.language, interaction.response_style, technical_preferences.development, writing_profile
- Storage/export policies per section
- Duplicate detection by target_path + value

### important_terms Removal (#132)
- Explicit removal workflow: shortened list → removal proposal
- Classified as Authorized Transformation (not Preserved)
- Explicit confirmation checkbox + reason required
- `_merge_important_terms` handles removal from profile
- Lineage records removed terms and operation type

### Lineage API/UI (#125)
- `CandidateLineage` model with events
- `BRIDGE_GET_CANDIDATE_LINEAGE` / `BRIDGE_GET_CAPTURE_LINEAGE`
- Side panel lineage display: Capture → Candidate → Evaluation → Decision → Target
- Operation type display (list_add/list_remove/persona_ir_split/user_revision)
- source_candidate_id tracking for edited/IR-split candidates

### i18n Compliance
- `docs/extension-i18n-coding-principles.md` defined and followed
- All logic uses structured data, not text matching
- Japanese/English locale files both maintained

### Context Portability Foundation (#141-148)
- Export: yaml / markdown / prompt with scope filtering
- ChatGPT-optimized markdown adapter
- Import: bundle → candidate diff → review flow
- Formation-layer ethics policy (private_raw / abstracted_effect / session_consent)
- Cross-LLM transfer test protocol
- RDE report template
- Golden tests (13 export tests, 5 guard tests)

### Storage Policy
- `CandidateStoragePolicy` model: storage_kind, target_path, prompt_export, sensitivity
- `promptExport: "never"` enforcement in prompt format

## Test Status

| Category | Count | Status |
|---|---|---|
| Unit tests (Python) | 313 passed | ✅ |
| Pre-existing failures | 7 | Not Phase 3 blockers (CLI env, xxx.yaml data, legacy MCP format) |
| Regression caused by Phase 3 | 0 new | ✅ |
| Golden tests (export) | 13 | ✅ |
| Guard tests (formation) | 5 | ✅ |
| Extension TS tests | 22 | ✅ |

## Known Issues (Not Blocking)

| Issue | Type | Phase |
|---|---|---|
| #86 Obsidian vault sync | Feature | Phase 5 |
| #87 Bridge daemon | Feature | Phase 6 |
| #78-81 OSS maintenance | Maintenance | Ongoing |

No critical bugs remain in Phase 3 scope.

## PR Summary

| PR | Issue | Description |
|---|---|---|
| #133 | #132 | important_terms removal workflow |
| #134 | #124 | Structured Persona IR Import |
| #135 | #119 | Edited Candidate creation |
| #136 | #125 | Lineage strengthening |
| #137 | #125 | Review session fallback |
| #139 | #138 | Accurate empty state |
| #140 | #138 | Judge-failed visibility |
| — | #120 | Classification tooltips |
| — | #141 | Export formats |
| — | #145 | Golden tests |
| — | #146 | ChatGPT adapter |
| — | #147 | RDE report template |
| — | #148 | Formation guard tests |

## Ready for Phase 4

Phase 4: Context Portability (export/import/transfer) is already partially implemented (#141-148). Next steps:

- #145 Golden test expansion
- #146 Claude/Gemini/DeepSeek adapters
- Cross-LLM transfer execution (A1/A2/A3)
- Import-to-Candidate integration with Bridge API
