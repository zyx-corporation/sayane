# ADR-001: T-RDE, TDD, and Design Pattern Principles

## Status

Accepted

## Date

2026-06-09

## Context

Chronicle Stack aims to record context, inputs, artifacts, decisions, revisions, diffs, and meaning changes that arise during human-AI collaboration.

The project is not merely a logging tool. Its purpose is to make it possible to reconstruct why an artifact exists, which context shaped it, which decision accepted or rejected it, and how its meaning changed across revisions.

Chronicle Core v0.1 introduces core records such as Chronicle Event, Context, Artifact, Artifact Version, Decision, and RDE Diff Record. These records are intended to support later layers such as Context Sovereignty, RDE integration, CSG-RAG, Sayane integration, dashboards, and research observability.

Because Chronicle Stack records human-AI collaboration history, implementation shortcuts can easily become hidden semantic claims. For example, a missing event reference may make an artifact version look detached from its actual decision path. A weakly linked RDE record may make a meaning-change audit appear complete even when it is not reconstructable. An export format may accidentally imply stronger review status than the underlying record supports.

Therefore, Chronicle Stack adopts three engineering principles from the beginning:

1. T-RDE, meaning RDE-oriented testing.
2. TDD, meaning Test-Driven Development.
3. Explicit design-pattern usage guided by portability, replaceability, and auditability.

## Decision

We will treat T-RDE, TDD, and design-pattern discipline as first-class architectural principles.

This ADR establishes the baseline rule:

> Every important feature must be testable at both the behavioral level and the meaning-reconstruction level.

In Chronicle Stack, a feature is not considered complete merely because it writes files, prints CLI output, or passes a happy-path test. It must also preserve or explicitly transform the relationships among context, event, artifact, version, decision, and RDE records under known constraints.

## T-RDE principle

T-RDE stands for RDE-oriented testing.

RDE here refers to Resonant Deviation Evaluator, a method for inspecting how meaning changes across transformation steps.

In Chronicle Stack, T-RDE is used to test whether a process changes a record, artifact, or interpretation in an acceptable, visible, and reconstructable way.

Typical targets include:

- event recording
- context registration
- artifact creation
- artifact versioning
- decision recording
- RDE Diff Record creation
- JSONL persistence
- index rebuilding
- search and export
- CLI command behavior
- schema conversion
- future graph projection
- future dashboard labels
- future CSG-RAG retrieval

T-RDE tests must ask:

1. What meaning was preserved?
2. What meaning was transformed?
3. What meaning was added?
4. What meaning was lost?
5. What unsupported claim may have been introduced?
6. What uncertainty or incompleteness must remain visible to the user?

For Chronicle Stack, these questions must be applied not only to natural-language artifacts but also to structural records. A broken reference is a semantic defect, not merely a technical defect.

## TDD principle

All core logic should be developed with tests first whenever practical.

TDD is required for:

- Chronicle Event model validation
- Artifact and Artifact Version persistence
- Decision recording
- RDE Diff Record recording
- JSONL append and read behavior
- corrupt JSONL handling
- index rebuild behavior
- search behavior
- export behavior
- CLI contracts
- error handling
- data-boundary logic
- future context-scope and visibility logic

TDD is strongly recommended for:

- Markdown and YAML rendering
- report formatting
- dashboard state transitions
- graph projection
- future CSG-RAG retrieval behavior
- future Sayane import and export

TDD is not required for throwaway experiments, but prototype code must not be silently promoted to the production path without tests.

## Test categories

The project should distinguish at least the following test categories.

### Unit tests

Used for deterministic functions and models.

Examples:

- ID prefix generation
- enum validation
- schema validation
- path construction
- JSONL line parsing
- Markdown report formatting
- error object serialization

### Service tests

Used for domain service behavior.

Examples:

- Chronicle initialization
- event recording
- context addition
- artifact creation
- artifact update
- artifact history reconstruction
- decision recording
- RDE recording
- index rebuild

### CLI integration tests

Used for command-level behavior.

Examples:

- `chronicle init`
- `chronicle record`
- `chronicle add-context`
- `chronicle artifact create`
- `chronicle artifact update`
- `chronicle artifact history`
- `chronicle decision record`
- `chronicle rde record`
- `chronicle search`
- `chronicle export`
- `chronicle index rebuild`

### Contract tests

Used for boundaries that must remain stable across refactoring.

Examples:

- JSONL event format
- metadata.yaml format
- artifact index format
- context index format
- decision index format
- RDE report format
- CLI JSON output format

### Golden tests

Used for stable representative examples.

Examples:

- a known Chronicle with one artifact, two versions, one decision, and one RDE record
- a known corrupted JSONL fixture
- a known Markdown export
- a known YAML export
- a known RDE report

### Regression tests

Used when a bug or semantic drift is discovered.

Every important correction should create or update a regression test.

Examples:

- an artifact version must not lose `source_event_id` after index rebuild
- a decision must not lose `event_id` after index rebuild
- an RDE record must remain discoverably linked to the target artifact version
- artifact update must not accidentally overwrite content with an empty body

### T-RDE tests

Used for meaning-preservation and meaning-change inspection.

Examples:

- An artifact version must remain linked to the event that produced it.
- A decision must remain linked to the event that recorded it.
- A rejected artifact must not be exported as accepted.
- A draft artifact must not be rendered as reviewed.
- An RDE record must not imply that all meaning-change fields were reviewed if they are empty.
- A rebuilt index must not invent stronger relationships than the JSONL primary record supports.
- A search result must not imply provenance that is absent from the stored event.

## Development phase gate

Every development phase must pass a planning gate before implementation begins.

A phase must not begin with direct coding on the main branch.

Before starting any non-trivial development phase, the following artifacts must exist:

1. a detailed phase description
2. one or more GitHub issues describing the work
3. an implementation branch created from the current main branch
4. initial test cases or test-case specifications
5. T-RDE acceptance criteria when the phase affects meaning, reconstruction, review status, provenance, or export interpretation
6. explicit assumptions and non-goals for the phase

This applies to all phases, including MVP phases.

Throwaway experiments may be performed separately, but they must not be merged into the production path unless they are converted into a phase with issues, branch, and tests.

## Issue requirement

Each development issue should include:

- purpose
- scope
- non-goals
- expected behavior
- expected meaning boundary
- test plan
- T-RDE checklist, when applicable
- design-pattern implications, when applicable
- completion criteria

If an issue affects stored relationships, review status, provenance, exported reports, or user-visible interpretation, it must explicitly state how it avoids overstating claims.

## Branch requirement

Each phase or non-trivial issue must be developed on a dedicated branch.

Recommended branch naming:

- `phase/<phase-name>`
- `feature/<short-feature-name>`
- `fix/<short-fix-name>`
- `docs/<short-doc-name>`
- `experiment/<short-experiment-name>`

The main branch should represent accepted project state.

Direct commits to main should be limited to repository initialization, urgent documentation corrections, or explicitly accepted administrative updates.

## Test-case requirement before implementation

Before implementation begins, the issue or branch must include at least one of the following:

- concrete failing tests
- executable test stubs
- fixture definitions
- golden examples
- contract examples
- T-RDE scenario descriptions

A phase that cannot yet define executable tests must define testable scenarios in prose before coding.

These scenarios must later be converted into executable tests before the feature is considered complete.

## Phase completion rule

A phase is complete only when:

1. the implementation satisfies the issue scope
2. all planned tests pass
3. new regression tests are added for discovered bugs
4. T-RDE acceptance criteria are reviewed, when applicable
5. documentation is updated
6. remaining uncertainty is documented
7. the branch is ready to merge or has been merged through the agreed review path

## Design-pattern usage principle

Design patterns should be used only when they improve clarity, replaceability, or auditability.

The project rejects ornamental pattern use.

Patterns are not architectural decoration. They are tools for keeping semantic, persistence, and implementation boundaries explicit.

## Recommended patterns

### Repository pattern

Use for persistence and external boundary access.

Examples:

- JsonlStore
- ArtifactStore
- IndexStore
- future ContextRepository
- future GraphRepository

Purpose:

- isolate storage behavior
- enable contract testing
- allow replacement of JSONL, SQLite, or graph storage
- prevent persistence details from leaking into domain logic

### Adapter pattern

Use for converting external or imported records into internal canonical models.

Examples:

- SayaneContextAdapter
- MarkdownArtifactAdapter
- ExternalConversationAdapter
- GitHubIssueAdapter

Purpose:

- prevent external schemas from leaking into Chronicle models
- make provenance-preserving conversion explicit
- support future import and export workflows

### Strategy pattern

Use for replaceable meaning-change, diff, export, and retrieval logic.

Examples:

- RdeEvaluationStrategy
- ArtifactDiffStrategy
- SearchStrategy
- ExportStrategy
- FutureContextSelectionStrategy

Purpose:

- allow algorithm replacement
- support A/B comparison of meaning-change logic
- keep assumptions testable

### Pipeline pattern

Use for multi-stage transformations.

Examples:

- ingest
- normalize
- record
- version
- evaluate
- index
- export

Purpose:

- make transformation stages explicit
- isolate failure modes
- support partial recomputation
- make semantic drift easier to locate

### Specification pattern

Use for validation, filtering, and policy-like conditions.

Examples:

- ArtifactExistsSpec
- VersionExistsSpec
- DecisionTargetExistsSpec
- NonEmptyArtifactContentSpec
- ExportVisibilitySpec
- FutureContextBoundarySpec

Purpose:

- make criteria auditable
- avoid hidden business logic inside CLI handlers
- prepare for future context-scope and visibility rules

### Observer / event pattern

Use for audit and observability events.

Examples:

- ChronicleCreated
- ContextAdded
- ArtifactCreated
- ArtifactVersioned
- DecisionRecorded
- RdeDiffRecorded

Purpose:

- support audit logs
- support future event-driven architecture
- make transformations traceable

### Factory pattern

Use sparingly for constructing replaceable stores, exporters, strategies, or future retrieval components.

Purpose:

- centralize creation of replaceable components
- avoid hard-coded dependencies
- keep tests simple

## Patterns to avoid by default

### Singleton

Avoid except for immutable configuration or explicitly controlled infrastructure handles.

Reason:

- makes tests harder
- hides dependency boundaries
- can create global state leaks

### Service Locator

Avoid.

Reason:

- hides dependencies
- weakens testability
- obscures architecture

### Over-layered architecture

Avoid premature abstraction.

Reason:

- Chronicle Core v0.1 is an MVP
- excessive layers can hide meaning transformations rather than clarify them
- v0.1 should keep JSONL, artifacts, decisions, and RDE records understandable

## Record design rule

No stored record may imply stronger review, provenance, or reconstruction status than the underlying data supports.

The following must remain separate:

- event occurrence
- artifact content
- artifact version
- decision status
- RDE evaluation
- review status
- provenance
- confidence
- trust

In particular:

- event existence is not human approval
- artifact creation is not acceptance
- artifact update is not review completion
- RDE record existence is not complete meaning validation
- confidence is not truth
- provenance is not correctness
- Delta-M is not value

Any code, CLI output, exported document, or future dashboard view that collapses these dimensions into a single unqualified status violates this ADR.

## Provenance and reconstructability rule

Every important derived view should be explainable by primary records.

A derived view should carry, or be linkable to:

- source Chronicle Events
- artifact versions
- decisions
- RDE records
- input timestamps
- generation or calculation version
- known limitations

The JSONL event log is the primary record in Chronicle Core v0.1.

Indexes are derived data. They may enrich lookup behavior, but they must not silently invent relationships that cannot be traced back to events or explicit derived rules.

If a relationship cannot be reconstructed, it must be marked missing, unresolved, or experimental rather than implied.

## CLI and report rule

The CLI and exported reports must not imply stronger claims than the stored records support.

Examples:

Incorrect:

- “Artifact accepted” when only `artifact_created` exists.
- “RDE complete” when all six RDE fields are empty.
- “Reviewed” when `review_status` is absent or `unreviewed`.
- “Source verified” when source metadata is missing.

Preferred:

- “Artifact created, no decision recorded.”
- “RDE record exists; no preserved/transformed/supplemented fields provided.”
- “Review status: unreviewed.”
- “Source reference unavailable.”

## Development workflow

For every non-trivial feature:

1. Define the expected behavior.
2. Define the expected meaning boundary.
3. Create or link the GitHub issue.
4. Create the implementation branch.
5. Define initial tests or test-case specifications.
6. Write tests where practical.
7. Implement the smallest working version.
8. Add regression tests for discovered bugs.
9. Document assumptions if the feature affects reconstruction, review, provenance, export, or interpretation.
10. Review T-RDE acceptance criteria before completion.

## Immediate application to Chronicle Core v0.1

The following areas are under this ADR immediately:

1. Artifact Version must persist its producing `source_event_id` in the primary record or in a clearly reconstructable way.
2. Decision must persist its recording `event_id` in the primary record or in a clearly reconstructable way.
3. RDE Diff Record must remain discoverably linked to the target Artifact Version.
4. Artifact update must not accidentally overwrite content with an empty body.
5. CLI behavior must be covered by integration tests.
6. CI must run the test suite on push and pull request.
7. Exported Markdown and YAML must not overstate review or RDE completion.

These requirements are not additional product scope. They are necessary to preserve the meaning of Chronicle Core v0.1.

## Consequences

### Benefits

- Chronicle history remains reconstructable.
- Event, artifact, decision, and RDE boundaries remain explicit.
- Bugs in semantic relationships become testable.
- Future CSG-RAG can rely on clean primary records.
- Future dashboard views can avoid overstating claims.
- Future Sayane import and export can preserve context boundaries.
- Development phases become reviewable before implementation begins.

### Costs

- More initial test and documentation work.
- Slower early prototyping for core logic.
- Need to maintain fixtures and golden examples.
- Need to distinguish primary records from derived indexes.
- Need to manage issues and branches even during early development.

## Non-goals

This ADR does not define final GraphRAG behavior.

This ADR does not mandate a specific database beyond Chronicle Core v0.1's JSONL primary record.

This ADR does not define dashboard UI behavior.

This ADR does not require all experimental sketches to follow production-grade TDD.

However, once prototype logic influences persisted records, exported documents, review status, provenance, or user-visible interpretation, it must be brought under this ADR.

## Related concepts

- Chronicle Stack
- Chronicle Core v0.1
- Context Sovereignty
- CSG-RAG
- Sayane
- RDE Diff Record
- Resonant Deviation Evaluator
- Delta-M
- Test-Driven Development
- Design patterns
- Provenance-aware systems
- Auditability
- Reconstructability
