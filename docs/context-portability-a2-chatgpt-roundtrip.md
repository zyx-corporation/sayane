# Context Portability A2: ChatGPT Round-Trip

## Status

**Complete. A2 ChatGPT-only round-trip successful.**

> Manual ChatGPT session: 2026-06-05.
> Return bundle: `docs/transfer-tests/a2-chatgpt-return.yml`

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
| Total candidates generated | **5** |
| Add (new section/value) | 5 |
| Update (changed value) | 0 |
| Duplicate (identical — no candidate) | 1 (identity) |
| Review required (inferred/uncertain) | 3 (writing, principles, execution_context) |

### Detailed Breakdown

| Section | Action | Notes |
|---|---|---|
| identity | **no candidate** | Identical to stored profile ✅ |
| interaction | add | tone as list → flat structure mismatch |
| writing | add | `inferred_candidate` — ChatGPT marked as inferred |
| technical | add | concepts as dict structure |
| principles | add | `inferred_candidate` — extracted, not literal |
| execution_context | add | `inferred_candidate` — reorganized from projects |

## Step 5: RDE Evaluation

### Preserved Elements

- **Identity**: name, preferred_name, roles — 100% preserved (duplicate confirmed)
- **Interaction**: language "ja", tone "precise, logical" — preserved
- **Technical**: RDE, Sayane concepts — preserved
- **Source metadata**: `source: chatgpt_roundtrip`, `llm_memory: false`, `roundtrip_stage: A2` — preserved

### Authorized Transformations

- tone list `["precise", "logical"]` restructured to flat dict — acceptable
- concepts moved under `technical.concepts` — acceptable

### Inferred Extensions

- **Writing style**: Marked as `inferred_candidate` with note — correctly self-annotated
- **Principles**: Marked as `inferred_candidate` — "not literal profile entries"
- **Execution context**: Reorganized from projects+comm data — marked as `inferred_candidate`

### Unresolved Gaps

- No explicit writing preferences in source profile
- No explicit execution_context section in source
- Structural mismatch between source sections and flat return YAML

### Suspicious Drift

- **None observed.** All inferred items carry `inferred_candidate` markers.

### Critical Distortion

- **None observed.**

## Step 6: Import Safety

| Check | Result |
|---|---|
| Import created Candidates, not direct merge | ✅ 5 candidates, 0 direct mutations |
| Source metadata preserved | ✅ metadata block intact |
| Uncertain items marked as candidates | ✅ 3/5 sections are `inferred_candidate` |
| No private/formation data leaked | ✅ |
| Lineage shows import source | ✅ `source: chatgpt_roundtrip` |
| Identity duplicate → no candidate | ✅ correctly excluded |

## Fixture Tests

| Test | Status |
|---|---|
| Parse return bundle metadata | ✅ |
| Identity duplicate → no candidate | ✅ |
| New sections generate candidates | ✅ |
| Metadata parsed for lineage | ✅ |
| Import does not mutate profile | ✅ |

## Decision

- [x] **A2 successful** → proceed to A2b (ChatGPT → Claude)
- [ ] A2 has issues → fix before A2b
- [ ] A2 failed → redesign round-trip protocol

## Recommendation

**Proceed to A2b: Sayane → ChatGPT → Claude → Sayane import.**

A2 confirmed:
1. Export produces usable bundle
2. ChatGPT understands return bundle format and self-annotates inferred content
3. Import generates candidates correctly — no silent merge
4. No critical distortion
5. Identity correctly duplicate-excluded

## Related

- `docs/transfer-tests/a2-chatgpt-source.md`
- `docs/transfer-tests/a2-chatgpt-return.yml`
- `tests/fixtures/context_portability/a2_chatgpt_return.yml`
- `tests/test_a2_roundtrip.py`
- `docs/context-portability-import.md`
- `docs/context-portability-a1-chatgpt-baseline.md`
- Issue #142, #143
