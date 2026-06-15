# ADR 0004: Python Code Size and Complexity Management Criteria

## Status

Proposed

## Date

2026-06-15

## Context

Python is easy to start writing and supports fast early development. However, as a codebase grows, multiple responsibilities can easily accumulate inside a single file, function, or class.

This becomes especially problematic when the following patterns appear:

- `main.py`, `app.py`, `service.py`, `manager.py`, or `utils.py` becomes large and ambiguous.
- CLI handling, configuration loading, database access, external API calls, domain logic, logging, and exception handling are mixed in the same module.
- Ambiguous `dict`-based data structures spread across multiple locations.
- Side-effectful operations and pure business decisions are not separated.
- Unit tests require large amounts of mocks or fixtures.
- Code that changes for different reasons is trapped in the same file, function, or class.

This is not merely a readability problem. It also makes the semantic change caused by a modification, or ΔM, harder to observe, test, and review.

Therefore, this project defines criteria for preventing Python code growth from turning into responsibility collapse. The criteria cover responsibility separation, dependency direction, complexity, and testability.

## Decision

Python code will not be split only by line count. Splitting and refactoring will be judged by change reason, dependency direction, testability, complexity, and semantic observability.

### 1. Split primarily by reason for change

Code that changes for the same reason may stay together. Code that changes for different reasons should be separated.

The following are generally different responsibilities:

- Configuration loading.
- CLI, Web API, or other input interfaces.
- Domain logic.
- Use-case orchestration.
- Database, file, external API, or other I/O.
- Logging configuration.
- Exception definitions.
- Data structure definitions.
- Test helper code.

### 2. Separate I/O from domain logic

Domain logic should not directly mix in the following concerns:

- `requests` or other HTTP clients.
- `sqlite3`, SQLAlchemy, or other database connections.
- Cloud SDKs such as `boto3`.
- `os.environ`.
- `pathlib` and file I/O.
- `print`.
- Current-time acquisition.
- Random number generation.

Side-effectful operations should live in adapters or infrastructure layers. The center of the system should contain pure functions or low-side-effect domain logic.

### 3. Fix dependency direction

The default dependency direction is:

```text
interfaces / cli / api
  ↓
usecases
  ↓
domain
```

External connections should live outside this core as adapters.

```text
adapters / infrastructure
  → conform to domain types and interfaces

domain
  → does not know adapters / infrastructure
```

If the domain layer starts depending directly on databases, HTTP clients, filesystems, cloud SDKs, or process environment, this is considered design degradation.

### 4. Use testability as a splitting criterion

The following signs indicate that a function, class, or module may have too many responsibilities:

- Unit tests require network access.
- Unit tests require a real database.
- Logic strongly depends on current time or environment variables.
- Too many mocks are required.
- Fixtures become large.
- One small change breaks a wide area of tests.

The target testing structure is:

```text
unit test:
  Verify pure functions and domain logic by input and output.

usecase test:
  Replace repositories and gateways with fakes.

integration test:
  Use configurations close to real databases, filesystems, or APIs.
```

### 5. Make types and data structures explicit

If the same `dict` shape is referenced in three or more places, consider one of the following:

- `dataclass`
- `TypedDict`
- Pydantic model
- domain model class

Use Pydantic when validating external input. Use `dataclass(frozen=True)` for internal immutable data structures when validation needs are modest.

### 6. Use classes only when state or shared dependencies justify them

A class is appropriate when one or more of the following are true:

- It owns state.
- Multiple methods share the same dependencies.
- A repository, gateway, or service dependency should be replaceable.
- Lifecycle management is required.
- It implements an abstract interface.

Do not use classes merely as containers for unrelated functions.

Avoid this pattern:

```python
class TextUtils:
    def normalize(self, text: str) -> str:
        return text.strip()
```

This should normally be a plain function.

### 7. Define complexity warning thresholds

The following are warning thresholds, not absolute prohibitions:

- One file: review splitting once it exceeds 300-500 lines.
- One function: review splitting once it exceeds 30-50 lines.
- One class: review splitting once it exceeds 200 lines.
- Function arguments: consider a dataclass or command object once there are more than 5 arguments.
- Nesting: consider early returns or function extraction beyond 3 levels.
- Cyclomatic complexity: review above 10, refactor by default above 20.

These thresholds trigger design review. They do not replace judgment.

### 8. Avoid god files

If files with the following names grow large, responsibility boundaries are probably unclear:

- `utils.py`
- `common.py`
- `helper.py`
- `service.py`
- `manager.py`
- `main.py`
- `app.py`

Prefer specific names:

```text
utils.py
  ↓
text_normalizer.py
date_range.py
retry_policy.py
json_codec.py
```

### 9. Prefer a lightweight layered layout for growing projects

For projects expected to grow beyond a small script, prefer a `src/` layout like this:

```text
project/
  pyproject.toml
  README.md
  src/
    myapp/
      __init__.py
      config.py
      domain/
        __init__.py
        models.py
        rules.py
        errors.py
      usecases/
        __init__.py
        register_user.py
      adapters/
        __init__.py
        repository_sqlite.py
        external_api.py
      interfaces/
        __init__.py
        cli.py
        web.py
      logging_config.py
  tests/
    unit/
    usecase/
    integration/
```

This layout is not mandatory for small scripts. Start layering when one or more of the following appear:

- More than one entry point exists.
- Web API support becomes likely.
- The persistence backend may change.
- There are two or more external APIs.
- Tests become hard to write.
- `utils.py` starts growing.
- Similar code is copied in multiple places.

### 10. Monitor complexity in CI

Recommended tools include:

- `ruff` for lint and formatting.
- `mypy` for type checking.
- `pyright` as an alternative or complement to `mypy`.
- `pytest` for tests.
- `radon` for cyclomatic complexity.
- `vulture` for unused code detection.
- `deptry` for dependency checks.

At minimum, CI should check:

- Lint passes.
- Formatting is consistent.
- Unit tests pass.
- Type checking passes.
- Complexity does not exceed warning thresholds without review.

## Consequences

### Positive

This policy should make it easier to:

- Limit the blast radius of changes.
- Write focused tests.
- Protect domain logic from side effects.
- Discover responsibility mixing during review.
- Prevent `utils.py` and `service.py` from becoming dumping grounds.
- Support future CLI, Web API, batch, and worker entry points.
- Observe semantic change, or ΔM, through tests.

### Negative

This policy also has costs:

- The number of files may increase earlier.
- Splitting can look excessive in small codebases.
- Developers unfamiliar with layering may face learning cost.
- Over-abstraction can make code harder to trace.
- Type and interface definitions may slow short-term development.

## Alternatives Considered

### Alternative 1: Operate mostly with single scripts

This is effective for small and short-lived scripts. However, it tends to break down when long-term maintenance, testing, automation, multiple entry points, or external integrations appear.

This project will not use this approach except for short-lived experimental code.

### Alternative 2: Adopt strict Clean Architecture from the beginning

This provides strong dependency direction and responsibility separation. However, in Python projects it can become over-engineered and slow down early development.

This project will borrow Clean Architecture principles but use lightweight layering rather than strict ceremony.

### Alternative 3: Split only by line count

This is simple to operate. However, short functions can still be complex, and long files can be acceptable when they contain simple data definitions.

Line count is therefore only a warning signal. The final decision depends on reason for change, dependency direction, testability, and complexity.

## RDE Review

### Preserved elements

This ADR preserves the following goals:

- Do not sacrifice Python's early development speed.
- Avoid premature over-engineering.
- Prioritize testability.
- Push side effects outward.
- Split by reason for change.
- Keep semantic change, or ΔM, observable.

### Transformed elements

The original problem of preventing code from becoming large is reframed as follows:

```text
code size problem
↓
responsibility boundary problem
↓
dependency direction problem
↓
testability problem
↓
semantic change observability problem
```

### Added elements

The ADR adds operational criteria for:

- Status.
- Context.
- Decision.
- Consequences.
- Alternatives considered.
- CI monitoring.
- Recommended directory layout.
- Complexity warning metrics.
- RDE review.

### Unresolved elements

These remain project-specific:

- Exact complexity thresholds.
- Whether `mypy`, `pyright`, or both are required.
- Whether Pydantic v2 is the default model layer.
- Whether repository and gateway interfaces use `Protocol` or abstract base classes.
- How much of this ADR applies to small scripts.

### Deviation risks

The main risks are:

- Splitting becomes an end in itself.
- File count increases without clearer semantic boundaries.
- The project drifts into over-abstracted Clean Architecture cosplay.
- Small scripts are forced into unnecessary structure.
- Type definitions become formal but fail to express real invariants.
- Refactoring improves appearance but not testability.

### Next update policy

Update this ADR after observing:

- Whether the complexity thresholds are realistic.
- Whether the splitting rules are usable in review.
- Which items CI can detect and which require human review.
- Whether the granularity of `domain`, `usecases`, `adapters`, and `interfaces` is appropriate.
- How RDE, TDD, and CI should work together.
- Concrete refactoring examples from files that actually became too large.

## Final Rule

Python code growth is treated not as a line-count problem, but as collapse of semantic boundaries.

Therefore, this project follows these principles:

- Separate things that change for different reasons.
- Push side effects outward.
- Keep domain code unaware of external dependencies.
- Treat hard-to-test code as a responsibility warning.
- Make semantic change, or ΔM, observable through tests.
