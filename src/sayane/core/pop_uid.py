"""PoP-UID linkage — explicitly deferred.

Irreversible binding between proof-of-personhood identifiers and authorization /
accountability history is prohibited at default settings. Future work may use
proof_of_existence / selective_disclosure as design analogies only.
"""

from __future__ import annotations

from sayane.core.authorization import AuthorizationFeatureFlags
from sayane.evaluators.authorization_guards import (
    PopUidLinkageDeferredError,
    assert_pop_uid_linkage_disabled,
    default_feature_flags,
)


def linkage_flags() -> AuthorizationFeatureFlags:
    return default_feature_flags()


def refuse_identity_authorization_join(
    *,
    operation: str = "join",
    flags: AuthorizationFeatureFlags | None = None,
) -> None:
    """Raise when PoP-UID linkage is attempted while feature remains disabled."""
    assert_pop_uid_linkage_disabled(flags, operation=operation)


__all__ = [
    "PopUidLinkageDeferredError",
    "linkage_flags",
    "refuse_identity_authorization_join",
]
