"""Integration checks for Phase 4 storage write policy."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from sayane.storage.candidates import save_candidate
from sayane.storage.lineage_store import append_record
from sayane.storage.security_policy import StorageSecurityError


def _candidate(candidate_id: str = "c-policy") -> CandidateUpdate:
    from datetime import UTC, datetime

    return CandidateUpdate(
        id=candidate_id,
        status="pending",
        target_profile_id="default",
        content="review-only candidate content",
        source=CandidateSource(type="test", uri=None, captured_at=datetime.now(UTC)),
        proposal=CandidateProposal(section="knowledge.concepts", add=[], summary=None),
    )


def test_candidate_write_allows_plain_local_home(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane-home")
    path = save_candidate(config, _candidate())
    assert path.exists()
    assert path.parent == config.candidates_dir


def test_candidate_write_blocks_git_home(tmp_path: Path) -> None:
    home = tmp_path / "repo-home"
    home.mkdir()
    (home / ".git").mkdir()
    config = BridgeConfig(home=home)
    with pytest.raises(StorageSecurityError) as exc:
        save_candidate(config, _candidate())
    assert exc.value.decision.reason == "git_worktree_on_hold"


def test_candidate_write_blocks_obsidian_home(tmp_path: Path) -> None:
    home = tmp_path / "vault-home"
    home.mkdir()
    (home / ".obsidian").mkdir()
    config = BridgeConfig(home=home)
    with pytest.raises(StorageSecurityError) as exc:
        save_candidate(config, _candidate())
    assert exc.value.decision.reason == "obsidian_vault_on_hold"


def test_lineage_write_allows_plain_local_home(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane-home")
    path = append_record(config, "default", "candidate_generated", {"candidate_id": "c1"})
    assert path.exists()


def test_lineage_write_blocks_external_sync_home(tmp_path: Path) -> None:
    home = tmp_path / "Dropbox" / "Sayane"
    config = BridgeConfig(home=home)
    with pytest.raises(StorageSecurityError) as exc:
        append_record(config, "default", "candidate_generated", {"candidate_id": "c1"})
    assert exc.value.decision.reason == "external_sync_on_hold"
