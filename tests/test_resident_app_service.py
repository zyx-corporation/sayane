"""Tests for ADR 0007 Phase 4 resident app service boundary."""

from __future__ import annotations

import pytest

from sayane.app.capabilities import CapabilityError, create_local_capability_token
from sayane.app.service import ResidentAppService
from sayane.bridge.config import BridgeConfig
from sayane.storage.repositories import build_test_repository_bundle


def test_capability_token_requires_declared_scope() -> None:
    token = create_local_capability_token(["review"])

    assert token.has("review") is True
    assert token.has("capture") is False
    with pytest.raises(CapabilityError, match="capture"):
        token.require("capture")


def test_admin_capability_implies_all_scopes() -> None:
    token = create_local_capability_token(["admin"])

    assert token.has("capture") is True
    assert token.has("review") is True
    assert token.has("mcp") is True


def test_resident_service_capture_requires_capture_capability(tmp_path) -> None:
    service = ResidentAppService()
    token = create_local_capability_token(["review"])
    config = BridgeConfig(home=tmp_path / "sayane")

    with pytest.raises(CapabilityError, match="capture"):
        service.capture_clipboard_as_candidate(
            "clipboard text",
            token=token,
            config=config,
        )


def test_resident_service_clipboard_capture_enters_candidate_repository(tmp_path) -> None:
    bundle = build_test_repository_bundle(profile_id="default")
    service = ResidentAppService(profile_id="default", repositories=bundle)
    token = create_local_capability_token(["capture"])
    config = BridgeConfig(home=tmp_path / "sayane")

    candidate = service.capture_clipboard_as_candidate(
        "important_terms:\n  - \"Sayane\"",
        token=token,
        config=config,
    )

    assert candidate.status == "pending"
    assert candidate.source.type == "clipboard"
    assert candidate.capture_meta is not None
    assert candidate.capture_meta.capture_source == "clipboard"
    assert bundle.candidates.load(candidate.id) == candidate
    assert bundle.profile_context is not None
    assert bundle.profile_context.load_context("profile") is None


def test_resident_service_repository_counts_require_admin(tmp_path) -> None:
    bundle = build_test_repository_bundle(profile_id="default")
    service = ResidentAppService(profile_id="default", repositories=bundle)
    capture_token = create_local_capability_token(["capture"])
    admin_token = create_local_capability_token(["admin"])
    config = BridgeConfig(home=tmp_path / "sayane")

    service.capture_clipboard_as_candidate(
        "clipboard text",
        token=capture_token,
        config=config,
    )

    with pytest.raises(CapabilityError, match="admin"):
        service.repository_counts(token=capture_token)

    assert service.repository_counts(token=admin_token) == {
        "profile_id": "default",
        "candidate_count": 1,
        "review_decision_count": 0,
        "lineage_count": 0,
    }


def test_resident_service_describe_does_not_expose_secret_state() -> None:
    service = ResidentAppService(
        profile_id="default",
        repositories=build_test_repository_bundle(profile_id="default"),
    )

    assert service.describe() == {
        "profile_id": "default",
        "has_repositories": True,
        "candidate_repository": True,
        "review_decision_repository": True,
        "lineage_repository": True,
    }
