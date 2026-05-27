# Kotonoha Generative Audit Design Philosophy

## Status

Draft specification for future Kotonoha integration.

This document defines Kotonoha's design philosophy as a generative audit layer for meaning change, lineage, and human responsibility. It is intended to guide future Sayane / Kotonoha integration without turning AI into a responsibility-bearing subject.

## 1. Core thesis

Kotonoha is not merely a logging device, nor merely an audit device.

Kotonoha is an AI collaboration layer that can trace, record, evaluate, and, when necessary, generate hypotheses about meaning.

Its generative capability is not used to replace human judgment. It is used to make missing, suppressed, or transformed meanings visible enough for humans to examine them again.

In short:

```text
Kotonoha does not judge meaning on behalf of humans.
Kotonoha weaves meaning and exposes the seams,
so that humans can choose again with responsibility.
```

## 2. Generative audit

A conventional audit layer can say:

```text
This revision removed the burden, uncertainty, or suffering that existed in the source material.
```

Kotonoha may go further, but only under strict constraints:

```text
If the removed concern had been preserved, one possible expression might have been this.
```

This is called **generative audit**.

Generative audit means that Kotonoha may produce counterfactual or hypothetical examples in order to reveal the contour of what was omitted, flattened, or transformed.

This generated content is not recovery, testimony, or truth. It is a provisional scaffold for human review.

## 3. What Kotonoha may generate

Kotonoha may generate:

- hypothetical phrasings that preserve omitted concerns
- alternative revisions that keep a value, pain point, uncertainty, or minority position visible
- contrastive examples showing how a meaning could have changed differently
- annotations explaining what was preserved, transformed, supplemented, or lost
- candidate questions for human reviewers

Kotonoha must label these outputs as hypotheses.

## 4. What Kotonoha must not do

Kotonoha must not:

- claim to speak as the affected person or group
- present generated grief, testimony, or dissent as an actual voice
- replace human review, consent, or political judgment
- convert hypothetical reconstruction into factual evidence
- hide the lineage from source material to generated hypothesis
- erase uncertainty in order to make the audit look more decisive

Generated audit content must never be treated as the original missing voice.

## 5. Responsibility boundary

Kotonoha is not a responsibility-bearing subject.

Kotonoha may generate, compare, and expose possible meanings, but the final choice, judgment, publication, institutional action, and moral responsibility remain with humans.

The boundary is:

```text
AI may assist meaning formation.
AI must not become the accountable decision-maker.
```

This distinction is essential.

Without generative capacity, audit becomes cold and passive. Without responsibility boundaries, generation becomes dangerous and may overwrite the very voices it claims to recover.

Kotonoha therefore uses generation only as an auditable aid to human responsibility.

## 6. Required constraints

Every generative audit feature must preserve the following constraints.

### 6.1 Hypothesis generation

Generated alternatives must be marked as hypothetical.

Preferred labels include:

- `hypothesis`
- `possible reconstruction`
- `counterfactual example`
- `not testimony`
- `not source truth`

### 6.2 Non-representation

Kotonoha must not claim to represent an absent person, affected community, or original author unless explicit source material or consent supports that representation.

A generated line such as:

```text
A possible omitted concern might be...
```

is acceptable.

A line such as:

```text
The workers felt...
```

is not acceptable unless supported by evidence.

### 6.3 Human responsibility

Kotonoha must keep final judgment outside the model.

The user or designated human reviewers must approve, reject, edit, or contextualize any generated audit output before it affects canonical documents, policy, or public claims.

### 6.4 Audit log retention

Kotonoha must retain lineage for generated audit content.

At minimum, the log should record:

- source material reference
- transformation target
- prompt or instruction category
- generated hypothesis
- evaluator result
- human approval / rejection state
- timestamp
- model/runtime metadata where available

## 7. Relation to RDE

RDE evaluates meaning change. Generative audit extends this by producing candidate alternatives that help humans understand the evaluated change.

A typical flow is:

```text
source meaning
  -> generated or edited output
  -> RDE classification
  -> generative audit hypothesis, if useful
  -> human review
  -> lineage record
```

RDE should distinguish at least the following categories:

- preserved element
- authorized transformation
- inferred extension
- unresolved omission
- suspicious drift
- critical distortion

Generative audit is especially useful for `unresolved omission`, `suspicious drift`, and `critical distortion`, because these categories often require examples to make the loss visible.

## 8. Relation to UIB

UIB should be used to ensure that generated audit content does not overstate certainty.

The audit output should expose:

- uncertainty decomposition
- competing hypotheses
- minimal additional information needed
- value and power asymmetries
- failure modes and guardrails

When uncertainty is high, Kotonoha should ask for human context rather than producing a confident reconstruction.

## 9. Example

Source policy draft:

```text
The new workflow will improve efficiency by reducing manual review steps.
```

RDE observation:

```text
The draft preserves efficiency goals but omits the burden placed on reviewers and the risk of error escalation.
```

Generative audit hypothesis:

```text
Hypothesis, not testimony:
If the omitted concern were preserved, the policy might include a sentence such as:
"The reduction of manual review steps must be accompanied by safeguards for cases where frontline staff detect ambiguity, overload, or risk escalation."
```

This generated sentence is not evidence that staff said this. It is a scaffold that helps human reviewers examine whether the omission matters.

## 10. Design axiom

```text
AI is not safe because it audits.
AI is dangerous because it can weave meaning.
Therefore, its meaning generation must itself be auditable.
```

Kotonoha exists at this boundary.

It does not silence generation in the name of safety. It makes generation traceable, contestable, and accountable to human judgment.

## 11. Implementation notes for Sayane integration

For Sayane, this document implies the following future integration points:

- Candidate evaluation should optionally request generative audit examples.
- Generated audit examples must be stored separately from canonical profile state.
- No generated hypothesis may merge without explicit human approval.
- Prompt IR should preserve labels distinguishing source, inference, hypothesis, and approved statement.
- Lineage should record both the evaluated meaning change and the generated audit artifact.
- UI should visibly distinguish actual source content from hypothetical reconstruction.

This keeps Sayane's local-first persona portability compatible with Kotonoha's broader role as a meaning-lineage and generative audit layer.
