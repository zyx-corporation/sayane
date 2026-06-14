"""Vault-backed repository bundle.

This module groups Vault-backed repositories for Candidate, ReviewDecision, and
Lineage records. It is the transition seam between Phase 4 local working stores
and the Phase 6 Local Vault backend.
"""

from __future__ import annotations

from dataclasses import dataclass

from sayane.storage.vault_candidates import VaultCandidateStore
from sayane.storage.vault_lineage import VaultLineageStore
from sayane.storage.vault_review_decisions import VaultReviewDecisionStore
from sayane.vault.contracts import UnlockSession, VaultStore, assert_vault_store_safe_for_production


@dataclass(frozen=True)
class VaultRepositoryBundle:
    """Grouped Vault-backed repositories for one profile."""

    profile_id: str
    vault: VaultStore
    candidates: VaultCandidateStore
    review_decisions: VaultReviewDecisionStore
    lineage: VaultLineageStore

    def require_safe_for_production(self) -> None:
        """Reject unsafe production defaults, such as plaintext production stores."""
        assert_vault_store_safe_for_production(self.vault)

    def smoke_check(self, *, session: UnlockSession) -> dict[str, int | str]:
        """Return non-secret repository counts for a scoped session.

        This is intended for tests and future diagnostics. It lists record ids
        and counts but does not expose plaintext content.
        """
        self.require_safe_for_production()
        return {
            "profile_id": self.profile_id,
            "candidate_count": len(self.candidates.list(session=session)),
            "review_decision_count": len(self.review_decisions.list(session=session)),
            "lineage_count": len(self.lineage.list(session=session)),
        }


def build_vault_repository_bundle(
    vault: VaultStore,
    *,
    profile_id: str = "default",
) -> VaultRepositoryBundle:
    """Build Vault-backed repositories for a profile."""
    bundle = VaultRepositoryBundle(
        profile_id=profile_id,
        vault=vault,
        candidates=VaultCandidateStore(vault, profile_id=profile_id),
        review_decisions=VaultReviewDecisionStore(vault, profile_id=profile_id),
        lineage=VaultLineageStore(vault, profile_id=profile_id),
    )
    bundle.require_safe_for_production()
    return bundle
