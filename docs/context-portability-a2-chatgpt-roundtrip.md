# Context Portability A2: ChatGPT Round-Trip

## Status

**Procedure documented. Awaiting manual ChatGPT session.**

## Purpose

Verify that context can survive a round-trip:
```
Sayane → export → ChatGPT → return bundle → Sayane import → Candidates
```

## Test Metadata

- **Test ID**: A2
- **Date**: 2026-06-05
- **Source**: `sayane export --scope identity,interaction,writing,technical,ethics --target chatgpt`
- **Round-trip**: ChatGPT (single LLM)
- **Prerequisites**: #141, #143, #153, #155

## Step 1: Export

```bash
sayane export \
  --format markdown \
  --scope identity,interaction,writing,technical,ethics \
  --target chatgpt \
  --profile examples/profiles/minimal.yaml \
  > docs/transfer-tests/a2-chatgpt-source.md
```

Source bundle saved at `docs/transfer-tests/a2-chatgpt-source.md`.

## Step 2: ChatGPT Prompt

Open a **fresh ChatGPT session**. Paste the entire source bundle, then paste:

```
You are receiving a Sayane external profile. It is not your memory.

Please produce a portable return bundle for Sayane import.

Requirements:
- Do not invent new user facts.
- Preserve only information explicitly present in the profile.
- Keep literal quotes as quotes.
- Do not convert interpretations into facts.
- Include metadata that this came from a ChatGPT round-trip.
- Separate identity, interaction, writing, technical, principles, and execution_context.
- Mark uncertain or inferred items explicitly as candidates.
- Output in YAML.

Return bundle shape:

metadata:
  source: "chatgpt_roundtrip"
  source_profile_type: "Sayane external profile"
  llm_memory: false
  target_for_import: "sayane"
  generated_by: "chatgpt"
  roundtrip_stage: "A2"
  uncertainty: "items are candidates, not canonical facts"

identity:
  name: "..."
  preferred_name: "..."
  roles: [...]

interaction:
  tone: "..."
  language: "..."

writing:
  # inferred from tone if not explicit
  style: "..."

technical:
  concepts: [...]

principles:
  - "..."

execution_context:
  # only if present in source
  projects: [...]

notes:
  inferred:
    - "..."
  unresolved:
    - "..."
  unchanged:
    - "..."
```

Save ChatGPT's response as `docs/transfer-tests/a2-chatgpt-return.yml`.

## Step 3: Import

```bash
sayane import-bundle docs/transfer-tests/a2-chatgpt-return.yml --profile examples/profiles/minimal.yaml
```

Or via Bridge API:

```bash
curl -X POST http://127.0.0.1:38741/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"path": "docs/transfer-tests/a2-chatgpt-return.yml", "profile_id": "default"}'
```

## Step 4: Candidate Review Results

| Category | Count |
|---|---|
| Total candidates generated | (fill) |
| Add (new section/value) | (fill) |
| Update (changed value) | (fill) |
| Duplicate (identical — no candidate) | (fill) |
| Review required (unknown section) | (fill) |

## Step 5: RDE Evaluation

### Preserved Elements

Original context that survived the round-trip:

- (fill)

### Authorized Transformations

Formatting or restructuring that preserved meaning:

- (fill)

### Inferred Extensions

What ChatGPT added beyond the exported context:

- (fill)

### Unresolved Gaps

Context lost, weakened, or made ambiguous:

- (fill)

### Suspicious Drift

Overstatement, generalization, or reinterpretation:

- (fill)

### Critical Distortion

Inversion or material misrepresentation:

- (fill)

## Step 6: Import Safety

| Check | Result |
|---|---|
| Import created Candidates, not direct merge | (fill) |
| Source metadata preserved | (fill) |
| Uncertain items marked as candidates | (fill) |
| No private/formation data leaked | (fill) |
| Lineage shows import source | (fill) |

## Fixture Tests

Automated tests in `tests/test_a2_roundtrip.py` (5 tests):

| Test | Status |
|---|---|
| Parse return bundle metadata | ✅ |
| Identity duplicate → no candidate | ✅ |
| New sections generate candidates | ✅ |
| Metadata parsed for lineage | ✅ |
| Import does not mutate profile | ✅ |

## Decision

- [ ] A2 successful → proceed to A2b (ChatGPT → Claude)
- [ ] A2 has issues → fix before A2b
- [ ] A2 failed → redesign round-trip protocol

## Recommendation

If ChatGPT-only round-trip succeeds:
→ **A2b: Sayane → ChatGPT → Claude → Sayane import**

If issues found:
→ Fix import parser for ChatGPT return bundle format first
→ Then proceed to multi-LLM

## Related

- `docs/transfer-tests/a2-chatgpt-source.md`
- `docs/transfer-tests/a2-chatgpt-return.yml` (after manual session)
- `tests/fixtures/context_portability/a2_chatgpt_return.yml`
- `tests/test_a2_roundtrip.py`
- `docs/context-portability-import.md`
- `docs/context-portability-a1-chatgpt-baseline.md`
- Issue #142, #143
