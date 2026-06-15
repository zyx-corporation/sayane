"""Tests for ADR 0007 Phase 4 resident app service boundary."""

from __future__ import annotations

import pytest

from sayane.app.capabilities import CapabilityError, create_local_capability_token
from sayane.app.service import ResidentAppService
from sayane.bridge.config import BridgeConfig
from sayane.storage.repositories import build_test_repository_bundle


def test_capability_token_requires_declared_scope() -> None:
    capability = create_local_capability_token(["review"])

    assert capability.has("review") is True
    assert capability.has("capture") is False
    with pytest.raises(CapabilityError, match="capture"):
        capability.require("capture")


def test_admin_capability_implies_all_scopes() -> None:
    capability = create_local_capability_token(["admin"])

    assert capability.has("capture") is True
    assert capability.has("review") is True
    assert capability.has("mcp") is True


def test_resident_service_capture_requires_capture_capability(tmp_path) -> None:
    service = ResidentAppService()
    capability = create_local_capability_token(["review"])
    config = BridgeConfig(home=tmp_path / "sayane")

    with pytest.raises(CapabilityError, match="capture"):
        service.capture_clipboard_as_candidate(
            "clipboard text",
            capability=capability,
            config=config,
        )


def test_resident_service_clipboard_capture_enters_candidate_repository(tmp_path) -> None:
    bundle = build_test_repository_bundle(profile_id="default")
    service = ResidentAppService(profile_id="default", repositories=bundle)
    capability = create_local_capability_token(["capture"])
    config = BridgeConfig(home=tmp_path / "sayane")

    candidate = service.capture_clipboard_as_candidate(
        "important_terms:\n  - \"Sayane\"",
        capability=capability,
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
    capture_capability = create_local_capability_token(["capture"])
    admin_capability = create_local_capability_token(["admin"])
    config = BridgeConfig(home=tmp_path / "sayane")

    service.capture_clipboard_as_candidate(
        "clipboard text",
        capability=capture_capability,
        config=config,
    )

    with pytest.raises(CapabilityError, match="admin"):
        service.repository_counts(capability=capture_capability)

    assert service.repository_counts(capability=admin_capability) == {
        "profile_id": "default",
        "candidate_count": 1,
        "review_decision_count": 0,
        "lineage_count": 0,
    }


def test_resident_service_describe_returns_public_shape() -> None:
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
