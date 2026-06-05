# A1: ChatGPT Transfer Baseline

> Cross-LLM transfer test: Sayane → ChatGPT
> Protocol: `docs/transfer-test-protocol.md`
> Template: `docs/transfer-tests/template.md`

## Test Info

- **Test ID**: A1
- **Date**: 2026-06-05
- **Source profile**: `examples/profiles/minimal.yaml`
- **Exported scopes**: identity, interaction, writing, technical
- **Target LLM**: ChatGPT
- **Export format**: markdown
- **Target adapter**: chatgpt (compact)
- **Bundle**: `docs/transfer-tests/a1-bundle.md`

## Exported Bundle

```
[Context — Sayane stored profile, not LLM memory — target: ChatGPT]

Identity: Name: Example User | Preferred: example | Roles: developer

Interaction: Language: ja | Tone: precise, logical

Concepts: RDE, Sayane
```

## Procedure

### Step 1: Open ChatGPT

Open a **fresh ChatGPT session** (new chat, no prior context).

### Step 2: Inject Context

Copy and paste the entire exported bundle (above) as the first message.
Do not add extra instructions or framing.

### Step 3: Task A — Context Recall

Ask:

> What do you know about me from the context I provided?

**Expected**: ChatGPT should reference the identity, interaction preferences, and concepts from the bundle. It should NOT fabricate details beyond what was provided.

**Record**: Note any fabricated or omitted details.

### Step 4: Task B — Style Adherence

Ask:

> Write a short technical explanation of what RDE means, in a style consistent with my interaction preferences.

**Expected**: Response should use precise, logical tone. Should reference RDE and Sayane concepts from context.

**Record**: Note tone matches, over-amplifications, or contradictions.

### Step 5: Task C — Value Summary

Ask:

> Summarize my interaction preferences and key concepts.

**Expected**: Accurate summary of identity, interaction style, and concepts.

**Record**: Note accuracy of each element.

### Step 6: RDE Evaluation

Fill in the [RDE Report](#rde-report) below using the recorded notes.

## RDE Report

> Fill in after completing Steps 3-6.

### Preserved

Elements accurately reflected by ChatGPT:

- [ ] Identity: Name "Example User"
- [ ] Identity: Preferred name "example"
- [ ] Identity: Roles "developer"
- [ ] Interaction: Language "ja"
- [ ] Interaction: Tone "precise, logical"
- [ ] Concepts: "RDE"
- [ ] Concepts: "Sayane"

### Authorized Transformation

Elements adapted but meaning preserved:

- (fill)

### Inferred Extension

Elements inferred beyond the provided context:

- (fill)

### Unresolved Gap

Context ignored or lost:

- (fill)

### Suspicious Drift

Response drifted from context:

- (fill)

### Critical Distortion

Meaning reversed or distorted:

- (fill)

## Portability Score (Experimental)

```text
Preserved:   /7
Authorized:  /0
Inferred:    count
Gap:         count
Drift:       count
Distortion:  count

Score = (Preserved + Authorized) / 7 = 
Loss  = (Gap + Drift + Distortion) / 7 = 
```

## Adapter Improvement Notes

- Bundle format observations:
- Prompt length / verbosity notes:
- Suggestions:

## Decision

- [ ] Transfer quality acceptable → proceed to A2
- [ ] Transfer has issues → improve adapter before A2
- [ ] Transfer failed → redesign bundle format
