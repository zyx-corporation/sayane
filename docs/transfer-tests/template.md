# RDE Portability Report

> Template for cross-LLM transfer test results.
> See `docs/transfer-test-protocol.md` for the full protocol.

## Test Info

- **Test ID**: (e.g. A1, A2, A3)
- **Date**: YYYY-MM-DD
- **Source profile**: 
- **Exported scopes**: 
- **Target LLM**: 
- **Export format**: markdown / prompt
- **Target adapter**: generic / chatgpt / claude / gemini

## RDE Evaluation

### Preserved

Elements accurately reflected by the target LLM:

- (list)

### Authorized Transformation

Elements adapted but meaning preserved:

- (list)

### Inferred Extension

Elements inferred beyond the provided context:

- (list)

### Unresolved Gap

Context ignored or lost:

- (list)

### Suspicious Drift

Response drifted from context:

- (list)

### Critical Distortion

Meaning reversed or distorted:

- (list)

## Portability Score (Experimental)

```text
Score = (Preserved + Authorized) / Total elements
Loss  = (Unresolved + Drift + Distortion) / Total elements
```

- **Score**: 
- **Loss**: 

## Notes

- Adapter improvement suggestions:
- Prompt format observations:
- Locale effects:

## Related

- `docs/transfer-test-protocol.md`
- `docs/adr/0001-context-portability-export-import.md`
- `docs/formation-layer-policy.md`
