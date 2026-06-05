# Context Portability: Claude Baseline Report

## Status

**Procedure documented. Awaiting manual Claude session.**

> Counterpart to A1: ChatGPT baseline.

## Test Metadata

- **Test ID**: Claude Baseline
- **Date**: 2026-06-05
- **Source**: Sayane external profile (`examples/profiles/minimal.yaml`)
- **Target**: Claude
- **Export format**: markdown
- **Target adapter**: claude (compact)
- **Scopes**: identity, interaction, writing, technical

## Export Command

```bash
sayane export \
  --format markdown \
  --scope identity,interaction,writing,technical \
  --target claude \
  --profile examples/profiles/minimal.yaml \
  > docs/transfer-tests/claude-baseline-source.md
```

Source bundle: `docs/transfer-tests/claude-baseline-source.md`

## Exported Bundle

```markdown
# Sayane External Profile for Claude

## Metadata
- Source: Sayane external profile
- LLM memory: false
- Target: Claude
- Scopes: identity, interaction, writing, technical

## How to Use This Context
This profile is external context supplied by Sayane.
It is not Claude memory.
Use it to guide responses within this session,
while respecting explicit uncertainty and avoiding unsupported assumptions.

## Identity
- Name: Example User
- Preferred name: example
- Roles: developer

## Interaction Preferences
- Language: ja
- Tone: precise, logical

## Principles
- RDE
- Sayane

## Technical Preferences
- RDE
- Sayane

## Export Policy Notes
- promptExport: never fields are not included.
```

## Receiving Session Conditions

- **Fresh Claude session**: Yes
- **Model**: (fill)
- **Manual paste**: Yes
- **Notes**: (fill)

## Claude Prompt

Paste the entire exported bundle, then paste:

```
You are receiving a Sayane external profile.

This profile is external context supplied by Sayane.
It is not your memory.
It is not a complete personality copy.
It is a portable context bundle for this session.

Please use it only as session-scoped external context.

Now answer the following four tasks:

1. Summarize the response style policy for this user.
2. Describe what should be preserved when answering technical
   design questions for this user.
3. Create a public-facing profile without private or
   formation-layer details.
4. Explain the idea of Sayane in under 800 Japanese characters.

Important rules:
- Do not invent new user facts.
- Preserve uncertainty.
- Keep literal quotes as quotes.
- Do not convert interpretations into facts.
- Do not treat this profile as your own memory.
- Do not include UI noise or transient session text.
```

## Fixed Tasks

### Task 1: Response Style Policy

> Summarize the response style policy for this user.

**Expected**: Identify tone (precise, logical), language (ja), external context boundary.

**Observed**: (fill)

### Task 2: Technical Design Constraints

> Describe what should be preserved when answering technical design questions.

**Expected**: Reference RDE, Sayane, explicit uncertainty.

**Observed**: (fill)

### Task 3: Public-Facing Profile

> Create a public-facing profile without private or formation-layer details.

**Expected**: Extract identity roles, exclude internal policy.

**Observed**: (fill)

### Task 4: Sayane Explanation (ja)

> Sayaneを800文字以内の日本語で説明してください。

**Expected**: Japanese response explaining context portability, external profile, audit.

**Observed**: (fill)

## Claude Response Summary

(fill — summarize overall response quality after manual session)

## RDE Evaluation

### Preserved Elements

- (fill)

### Authorized Transformations

- (fill)

### Inferred Extensions

- (fill)

### Unresolved Gaps

- (fill)

### Suspicious Drift

- (fill)

### Critical Distortion

- (fill)

## Comparison with ChatGPT A1

| Axis | ChatGPT A1 | Claude Baseline |
|---|---|---|
| External profile boundary | ✅ Recognized | (fill) |
| Japanese response style | ✅ Used | (fill) |
| Technical constraints | ✅ Preserved | (fill) |
| Quote preservation | ✅ Axioms quoted | (fill) |
| Principles handling | ✅ Section rendered | (fill) |
| Execution context | ✅ Separated | (fill) |
| Noise sensitivity | ⚠️ Noted (→#155) | (fill) |
| Critical distortion | None | (fill) |

## Adapter Improvement Notes

- (fill — changes needed for Claude adapter based on observed response)

## Readiness Judgment

- Claude target adapter baseline usable: **yes / no / partial**
- Ready for A2b ChatGPT → Claude round-trip: **yes / no / conditional**

## Decision

- [ ] Claude baseline usable → proceed to A2b
- [ ] Claude baseline partial → fix adapter then A2b
- [ ] Claude baseline failed → investigate before A2b

## Related

- `docs/transfer-tests/claude-baseline-source.md`
- `docs/context-portability-a1-chatgpt-baseline.md`
- `docs/context-portability-a2-chatgpt-roundtrip.md`
- Issue #142
