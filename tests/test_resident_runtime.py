"""Tests for resident runtime builder (#180)."""

from __future__ import annotations

from sayane.app.runtime import ResidentRuntime, build_resident_runtime
from sayane.storage.repositories import build_test_repository_bundle


def test_resident_runtime_describes_service_and_bridge_config(tmp_path) -> None:
    runtime = build_resident_runtime(
        home=tmp_path / "sayane",
        host="127.0.0.1",
        port=39000,
    )

    assert isinstance(runtime, ResidentRuntime)
    assert runtime.bridge_config.home == tmp_path / "sayane"
    assert runtime.bridge_config.host == "127.0.0.1"
    assert runtime.bridge_config.port == 39000
    assert runtime.describe() == {
        "profile_id": "default",
        "has_repositories": False,
        "candidate_repository": False,
        "review_decision_repository": False,
        "lineage_repository": False,
        "bridge_host": "127.0.0.1",
        "bridge_port": 39000,
        "capabilities": ["admin", "capture"],
    }


def test_resident_runtime_accepts_explicit_repository_bundle(tmp_path) -> None:
    bundle = build_test_repository_bundle(profile_id="default")
    runtime = build_resident_runtime(
        home=tmp_path / "sayane",
        repositories=bundle,
    )

    assert runtime.service.repositories is bundle
    assert runtime.describe()["has_repositories"] is True
    assert runtime.describe()["candidate_repository"] is True


def test_resident_runtime_capabilities_are_separate() -> None:
    runtime = build_resident_runtime()

    assert runtime.capabilities["capture"].has("capture") is True
    assert runtime.capabilities["capture"].has("admin") is False
    assert runtime.capabilities["admin"].has("capture") is True
    assert runtime.capabilities["admin"].has("review") is True
