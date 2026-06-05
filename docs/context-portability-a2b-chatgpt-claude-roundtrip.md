# Context Portability A2b: ChatGPT → Claude → Sayane Import

## Status

**Procedure documented. Awaiting manual Claude session.**

## Purpose

First multi-LLM round-trip:
```
Sayane → export → ChatGPT → return bundle → Claude → return bundle → Sayane import
```

Verify whether context survives two LLM transitions. Primary risk: Claude upgrades ChatGPT-inferred content into canonical facts.

## Prerequisites

- [x] A1 ChatGPT baseline (#142)
- [x] A2 ChatGPT-only round-trip
- [x] Claude baseline (#157 corrected)
- [x] Import hygiene (#156)

## Step 1: Source Bundle

The ChatGPT return bundle from A2 serves as input to Claude:
`docs/transfer-tests/a2-chatgpt-return.yml`

Key characteristics of this bundle:
- Contains `inferred_candidate` markers (ChatGPT self-annotated)
- Has placeholder identity (`Example User`) — import filters this
- Contains metadata: `source: chatgpt_roundtrip`, `llm_memory: false`

## Step 2: Claude Prompt

Open a **fresh Claude session**. Paste:

```
You are receiving a Sayane external profile that was produced by ChatGPT
during a Context Portability round-trip test.

This profile is external context.
It is not your memory.
It is not a complete user personality.
It contains inferred and uncertain items marked as candidates.

Sayane is the external context portability system.
It is not your name, identity, or memory.

ChatGPT is the source of this specific bundle.
It is not your identity either.

Rules:
- Do not treat this bundle as your own memory or as canonical user facts.
- Do not upgrade uncertain or inferred items into facts.
- Preserve the distinction between provided context and inference.
- If ChatGPT-inferred content appears, keep it marked as inferred.
- Do not invent new user facts.
- Do not merge ChatGPT, Claude, Sayane, or user identity.

Now produce a Sayane import return bundle in YAML.

Required metadata:

metadata:
  source: "a2b_chatgpt_claude_roundtrip"
  upstream_source: "chatgpt_roundtrip"
  source_profile_type: "Sayane external profile"
  llm_memory: false
  target_for_import: "sayane"
  generated_by: "claude"
  roundtrip_stage: "A2b"
  uncertainty: "items are candidates, not canonical facts"
  boundary_note: "This bundle passed through ChatGPT before reaching Claude. Both are separate external systems. Neither is the user's canonical context."

Required sections (use only data present in the provided bundle):

identity:
  # Verify: did ChatGPT preserve original identity or use placeholder?
  name: "..."
  preferred_name: "..."
  roles: [...]

interaction_style:
  language: "..."
  tone: [...]

response_policy:
  prefer: [...]
  avoid: [...]

technical:
  preferences: [...]

principles:
  - "..."

philosophical_stance:
  axioms:
    - quote: "..."
      interpretation: "..."

inferred_or_uncertain:
  # Items that were marked as inferred by ChatGPT
  # or that Claude cannot confirm from the provided context alone
  items: [...]

identity_boundary_check:
  sayane_is_context_system: true
  chatgpt_is_not_user: true
  claude_is_not_user: true
  profile_is_external: true
  profile_is_not_memory: true

notes:
  preserved_from_upstream:
    - "..."
  upstream_inferred_kept_as_inferred:
    - "..."
  new_inferred_by_claude:
    - "..."
  unresolved:
    - "..."
  rde_hint: "If ChatGPT's original content was uncertain, Claude should not strengthen it."
```

Save Claude's response as `docs/transfer-tests/a2b-claude-return.yml`.

## Evaluation Focus

### 1. External Profile Boundary
- Does Claude preserve that the profile is external context?
- Does it avoid treating imported content as its own memory?

### 2. Assistant Identity Boundary
- Does Claude distinguish Sayane, ChatGPT, Claude, and the user?
- Does it avoid merging Sayane into the assistant identity?

### 3. Factual Preservation
- Does Claude preserve only facts present in the provided bundle?
- Does it avoid inventing user facts or strengthening uncertain claims?

### 4. Uncertainty Preservation
- Are inferred/uncertain items still marked as uncertain?
- Are interpretations not converted into facts?

### 5. Technical Constraint Preservation
- Context Portability, Candidate Review, lineage, external profile, import/export boundary?

### 6. Import Suitability
- Is the returned YAML structurally valid?
- Suitable for `sayane import-bundle` without manual repair?

### 7. RDE / ΔM Check

#### Preserved Elements
- (fill after session)

#### Authorized Transformations
- (fill after session)

#### Inferred Extensions
- (fill after session)

#### Suspicious Drift
- Critical risk: Claude upgrades ChatGPT-inferred content into canonical facts
- (fill after session)

#### Critical Distortion
- (fill after session)

## Judgment

| Outcome | Criteria |
|---|---|
| ✅ Usable | No critical distortion, uncertainty preserved, boundaries maintained |
| ⚠️ Usable with notes | Small terminology drift, no identity/memory boundary violation |
| ❌ Not usable | Assistant identity, memory boundary, or user facts merged incorrectly |

## Import Test

After Claude session, import the result:

```bash
sayane import-bundle docs/transfer-tests/a2b-claude-return.yml --profile examples/profiles/minimal.yaml
```

## Related

- `docs/transfer-tests/a2-chatgpt-return.yml`
- `docs/context-portability-a1-chatgpt-baseline.md`
- `docs/context-portability-claude-baseline.md`
- `docs/context-portability-a2-chatgpt-roundtrip.md`
- Issue #142
