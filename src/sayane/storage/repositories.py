"""Repository contracts for resident app and local vault state.

ADR 0007 introduces repository boundaries so CLI, Bridge, MCP, and future
resident UI surfaces can share durable Candidate, ReviewDecision, Lineage,
and context state without each owning process-local stores.

The in-memory implementations in this module are test/development seams only.
They are not production persistence and must not become the default resident
app state store.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Protocol, runtime_checkable

from sayane.core.candidate import CandidateUpdate
from sayane.core.review_decision import ReviewDecision


@runtime_checkable
class CandidateRepository(Protocol):
    """Repository contract for CandidateUpdate records."""

    def save(self, candidate: CandidateUpdate, **kwargs: Any) -> str:
        """Persist one candidate and return its id."""

    def load(self, candidate_id: str, **kwargs: Any) -> CandidateUpdate | None:
        """Load one candidate by id."""

    def list(self, **kwargs: Any) -> list[CandidateUpdate]:
        """List candidates visible to this repository scope."""

    def delete(self, candidate_id: str, **kwargs: Any) -> None:
        """Delete one candidate by id."""


@runtime_checkable
class ReviewDecisionRepository(Protocol):
    """Repository contract for human review decisions."""

    def append(self, decision: ReviewDecision, **kwargs: Any) -> str:
        """Persist one review decision and return its record id."""

    def list(self, **kwargs: Any) -> list[ReviewDecision]:
        """List review decisions visible to this repository scope."""

    def get(self, record_id: str, **kwargs: Any) -> ReviewDecision | None:
        """Load one review decision by record id."""


@runtime_checkable
class LineageRepository(Protocol):
    """Append-only lineage repository contract."""

    def append(self, event: str, payload: dict[str, Any], **kwargs: Any) -> str:
        """Append one lineage event and return its record id."""

    def list(self, **kwargs: Any) -> list[dict[str, Any]]:
        """List lineage events visible to this repository scope."""

    def get(self, record_id: str, **kwargs: Any) -> dict[str, Any] | None:
        """Load one lineage event by record id."""


@runtime_checkable
class ProfileContextRepository(Protocol):
    """Repository contract for profile-scoped context documents/state."""

    def load_context(self, key: str, **kwargs: Any) -> dict[str, Any] | None:
        """Load one profile context payload by key."""

    def save_context(self, key: str, payload: dict[str, Any], **kwargs: Any) -> None:
        """Persist one profile context payload by key."""


@runtime_checkable
class ProjectContextRepository(Protocol):
    """Repository contract for project-scoped context documents/state."""

    def load_context(
        self,
        project_id: str,
        key: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Load one project context payload by project and key."""

    def save_context(
        self,
        project_id: str,
        key: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Persist one project context payload by project and key."""


class TestOnlyInMemoryCandidateRepository:
    """Test-only in-memory CandidateRepository implementation."""

    def __init__(self) -> None:
        self._candidates: dict[str, CandidateUpdate] = {}

    def save(self, candidate: CandidateUpdate, **kwargs: Any) -> str:
        _ = kwargs
        self._candidates[candidate.id] = candidate
        return candidate.id

    def load(self, candidate_id: str, **kwargs: Any) -> CandidateUpdate | None:
        _ = kwargs
        return self._candidates.get(candidate_id)

    def list(self, **kwargs: Any) -> list[CandidateUpdate]:
        _ = kwargs
        return list(self._candidates.values())

    def delete(self, candidate_id: str, **kwargs: Any) -> None:
        _ = kwargs
        self._candidates.pop(candidate_id, None)


class TestOnlyInMemoryReviewDecisionRepository:
    """Test-only in-memory ReviewDecisionRepository implementation."""

    def __init__(self) -> None:
        self._decisions: dict[str, ReviewDecision] = {}

    def append(self, decision: ReviewDecision, **kwargs: Any) -> str:
        _ = kwargs
        record_id = decision.lineage_event_id
        self._decisions[record_id] = decision
        return record_id

    def list(self, **kwargs: Any) -> list[ReviewDecision]:
        _ = kwargs
        return list(self._decisions.values())

    def get(self, record_id: str, **kwargs: Any) -> ReviewDecision | None:
        _ = kwargs
        return self._decisions.get(record_id)


class TestOnlyInMemoryLineageRepository:
    """Test-only in-memory LineageRepository implementation."""

    def __init__(self) -> None:
        self._events: dict[str, dict[str, Any]] = {}

    def append(self, event: str, payload: dict[str, Any], **kwargs: Any) -> str:
        _ = kwargs
        record_id = str(payload.get("event_id") or payload.get("id") or len(self._events) + 1)
        self._events[record_id] = {"event": event, **payload, "event_id": record_id}
        return record_id

    def list(self, **kwargs: Any) -> list[dict[str, Any]]:
        _ = kwargs
        return list(self._events.values())

    def get(self, record_id: str, **kwargs: Any) -> dict[str, Any] | None:
        _ = kwargs
        return self._events.get(record_id)


class TestOnlyInMemoryProfileContextRepository:
    """Test-only in-memory ProfileContextRepository implementation."""

    def __init__(self) -> None:
        self._contexts: dict[str, dict[str, Any]] = {}

    def load_context(self, key: str, **kwargs: Any) -> dict[str, Any] | None:
        _ = kwargs
        payload = self._contexts.get(key)
        if payload is None:
            return None
        return dict(payload)

    def save_context(self, key: str, payload: dict[str, Any], **kwargs: Any) -> None:
        _ = kwargs
        self._contexts[key] = dict(payload)


class TestOnlyInMemoryProjectContextRepository:
    """Test-only in-memory ProjectContextRepository implementation."""

    def __init__(self) -> None:
        self._contexts: dict[tuple[str, str], dict[str, Any]] = {}

    def load_context(
        self,
        project_id: str,
        key: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        _ = kwargs
        payload = self._contexts.get((project_id, key))
        if payload is None:
            return None
        return dict(payload)

    def save_context(
        self,
        project_id: str,
        key: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        _ = kwargs
        self._contexts[(project_id, key)] = dict(payload)


def review_decision_to_payload(decision: ReviewDecision) -> dict[str, Any]:
    """Return a JSON-like payload for repository adapter tests and migrations."""
    return asdict(decision)
