# Contributing to Sayane

Thank you for contributing to Sayane.

Sayane is a local-first tool for portable persona/context workflows across LLM runtimes. Because it handles user context, we treat changes as semantic changes, not only code changes.

## 1. Core principles

```text
RDE-oriented development
Issue first
Branch first
TDD / test first
Design-pattern conscious architecture
Security / Privacy by design
```

See also:

- `docs/development-principles.md`
- `docs/ui-design-principles.md` — Extension / 対話 UI の busy・カーソル・状態表示
- `docs/mvp-scope.md`
- `docs/security.md`
- `docs/roadmap.md`

## 2. Contribution flow

### 2.1 Issue first

Start implementation/fixes/design/docs from an Issue whenever possible.

Include:

- goal
- background
- in-scope
- out-of-scope
- acceptance criteria
- RDE considerations
- test strategy

Use the existing Issue templates.

### 2.2 Branch first

Do not push directly to `main`.

Recommended branch naming:

```text
feature/<issue-number>-<short-name>
fix/<issue-number>-<short-name>
docs/<issue-number>-<short-name>
refactor/<issue-number>-<short-name>
test/<issue-number>-<short-name>
```

Examples:

```text
feature/9-python-package-setup
docs/18-mcp-server-design
fix/24-profile-diff-classification
```

### 2.3 TDD / test first

For Core/CLI/Adapter/Evaluator/Storage changes, write tests first whenever feasible.

```text
Red      : write a failing test
Green    : make it pass with minimal implementation
Refactor : improve design and readability
RDE Review: verify semantic impact
```

### 2.4 Pull Request

Follow the PR template and include:

- related Issue
- change summary
- tests run
- RDE review
- design-pattern notes
- security/privacy checks
- compatibility impact
- docs update status

## 3. RDE review

In Sayane, each change is a semantic change.

When possible, review PRs with:

```text
Preserved
Authorized Transformation
Inferred Extension
Unresolved Gap
Suspicious Drift
Critical Distortion
```

Avoid:

- making claims stronger than the originating Issue
- presenting unverified behavior as proven
- justifying design principles from implementation convenience only
- unintentionally changing the meaning of Profile / Prompt IR / Lineage
- implying perfect persona reproduction
- introducing automatic profile updates without explicit user approval

## 4. Design patterns

Sayane explicitly relies on patterns to handle runtime/UI/storage/evaluation differences.

Typical patterns:

- Adapter
- Strategy
- Builder
- Factory
- Decorator
- Observer
- Repository

When adding a feature, clarify responsibilities and layer placement.

## 5. Security / Privacy

Sayane profiles may contain sensitive data.

Do not:

- commit secrets/tokens/API keys/private keys
- include real sensitive data in logs or fixtures
- weaken auth boundaries of Local Bridge or MCP Server
- merge captured content into profile without approval
- dangerously overwrite identity/values/policy/profile fields

See `docs/security.md` for details.

## 6. Phase-1 priority

For early implementation, prioritize Phase-1 CLI MVP.

Suggested order:

```text
#9  Project skeleton and Python package setup
#10 SayaneProfile schema and Pydantic model
#11 PromptIR model and builder
#12 Adapter interface and ChatGPT / Claude adapters
#13 CLI commands for init / inspect / compile / export
#14 Examples and documentation for CLI MVP
```

Phase 1 does not include Local Bridge, MCP Server, Chrome Extension, or automated RDE/UIB evaluation.

## 7. License

Sayane is distributed under Apache License 2.0.

By contributing code/docs/tests/configuration, you agree they are provided under Apache-2.0 unless explicitly stated otherwise.

SPDX-License-Identifier: Apache-2.0
