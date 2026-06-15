"""Resident app service boundary.

The service coordinates future resident UI operations through explicit
capability checks and repository/usecase seams. It must not become a direct
SQLite, Bridge-route, or UI-state owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sayane.app.capabilities import CapabilityToken
from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import CaptureMetadata, CandidateUpdate
from sayane.storage.repositories import RepositoryBundle


@dataclass(frozen=True)
class ResidentAppService:
    """Minimal resident app service seam for ADR 0007 Phase 4."""

    profile_id: str = "default"
    repositories: RepositoryBundle | None = None

    def describe(self) -> dict[str, Any]:
        """Return non-secret resident app runtime capabilities."""
        return {
            "profile_id": self.profile_id,
            "has_repositories": self.repositories is not None,
            "candidate_repository": self.repositories is not None,
            "review_decision_repository": self.repositories is not None,
            "lineage_repository": self.repositories is not None,
        }

    def capture_clipboard_as_candidate(
        self,
        text: str,
        *,
        token: CapabilityToken,
        config: BridgeConfig | None = None,
        locale: str | None = None,
        repository_kwargs: dict[str, Any] | None = None,
    ) -> CandidateUpdate:
        """Capture explicit clipboard text as a pending Candidate.

        Clipboard capture remains a Candidate flow. It does not write directly
        to profile or project context.
        """
        token.require("capture")
        from sayane.storage.candidates import create_from_capture

        cfg = config or BridgeConfig()
        candidate = create_from_capture(
            cfg,
            content=text,
            source_type="clipboard",
            raw_content=text,
            profile_id=self.profile_id,
            locale=locale,
            capture_meta=CaptureMetadata(
                user_selected=True,
                capture_source="clipboard",
                capture_confidence="high",
            ),
        )
        if self.repositories is not None:
            self.repositories.candidates.save(candidate, **(repository_kwargs or {}))
        return candidate

    def repository_counts(self, *, token: CapabilityToken, **kwargs: Any) -> dict[str, int | str]:
        """Return non-secret repository counts for diagnostics."""
        token.require("admin")
        if self.repositories is None:
            return {
                "profile_id": self.profile_id,
                "candidate_count": 0,
                "review_decision_count": 0,
                "lineage_count": 0,
            }
        return {
            "profile_id": self.profile_id,
            "candidate_count": len(self.repositories.candidates.list(**kwargs)),
            "review_decision_count": len(self.repositories.review_decisions.list(**kwargs)),
            "lineage_count": len(self.repositories.lineage.list(**kwargs)),
        }
