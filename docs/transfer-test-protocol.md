# Cross-LLM Transfer Test Protocol

## Purpose

Define a repeatable protocol for testing Context Portability across LLMs using Sayane export bundles and RDE evaluation.

## Test A1: ChatGPT Transfer Baseline

### Prerequisites

- Sayane profile with identity, interaction, technical, and writing context
- `sayane export` command available
- Fresh ChatGPT session

### Steps

1. **Prepare context**: Use an existing profile or the minimal fixture at `examples/profiles/minimal.yaml`.

2. **Export bundle**:
   ```bash
   sayane export --format markdown --scope identity,interaction,technical,writing --target chatgpt
   ```

3. **Inject into ChatGPT**: Paste the markdown output into a fresh ChatGPT session. Do not add extra instructions.

4. **Task prompts** (ask in order):
   - "What do you know about me from the context provided?"
   - "Write a short response to a technical question in a style consistent with my interaction preferences."
   - "Summarize my key values and interaction preferences."

5. **Evaluate with RDE axes**:

| Axis | Check |
|---|---|
| Preserved | Which context elements were accurately reflected? |
| Authorized Transformation | Which elements were adapted but meaning preserved? |
| Inferred Extension | What did the LLM infer beyond the provided context? |
| Unresolved Gap | What context was ignored or lost? |
| Suspicious Drift | Where did the response drift from the context? |
| Critical Distortion | Was any context meaningfully reversed or distorted? |

6. **Record results** in `docs/transfer-tests/a1-chatgpt-baseline.md`.

### Expected output format

```markdown
# A1: ChatGPT Transfer Baseline

Date: YYYY-MM-DD
Exported scopes: identity, interaction, technical, writing
Target: chatgpt

## Preserved
- (list elements correctly preserved)

## Authorized Transformation
- (list adapted but meaning-preserved elements)

## Inferred Extension
- (list inferred elements beyond context)

## Unresolved Gap
- (list ignored/lost context)

## Suspicious Drift
- (list drift from context)

## Critical Distortion
- (list meaning reversals/distortions)

## Notes
- (adapter improvement notes, prompt format suggestions)
```

## Test A2: Round-Trip Transfer

### Steps

1. Export from profile with `--target claude`
2. Inject into Claude session
3. Ask Claude to summarize the context back
4. Copy Claude's summary
5. Inject summary into ChatGPT
6. Ask ChatGPT questions about the context
7. Evaluate both transitions with RDE axes

### Record

Save to `docs/transfer-tests/a2-roundtrip-claude-chatgpt.md`.

## Test A3: Multi-LLM Expansion

Future targets: Gemini, DeepSeek, Open WebUI.

Each expansion follows the A1 protocol with target-specific export.

## RDE Portability Score (Experimental)

For quantitative tracking:

```text
Score = (Preserved + Authorized) / (Total elements)
Loss = (Unresolved + Drift + Distortion) / (Total elements)
```

This score is a rough heuristic only. Qualitative notes are the primary evaluation.

## Automated Test Script

A script at `scripts/transfer-test.sh` runs the export step and validates bundle format:

```bash
#!/usr/bin/env bash
# Transfer test helper: export and validate bundle
set -euo pipefail
PROFILE="${1:-examples/profiles/minimal.yaml}"
SCOPES="${2:-identity,interaction,technical}"
TARGET="${3:-chatgpt}"
FORMAT="${4:-markdown}"
sayane export --format "$FORMAT" --scope "$SCOPES" --target "$TARGET" --profile "$PROFILE"
```
