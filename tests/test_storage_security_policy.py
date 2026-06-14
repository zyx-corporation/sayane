"""Tests for Phase 4 FileSystem storage security policy."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.storage.security_policy import (
    StorageSecurityError,
    StorageSecurityPolicy,
    default_storage_security_policy,
    require_local_working_store,
)


def test_default_policy_allows_plain_local_working_store(tmp_path: Path) -> None:
    path = tmp_path / "profiles" / "default" / "candidates.jsonl"
    decision = require_local_working_store(path, record_class="candidate")
    assert decision.allowed is True
    assert decision.reason == "local_filesystem_allowed"


def test_default_policy_blocks_git_worktree_for_candidate_records(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    path = root / "profiles" / "default" / "candidates.jsonl"
    with pytest.raises(StorageSecurityError) as exc:
        require_local_working_store(path, record_class="candidate")
    assert exc.value.decision.reason == "git_worktree_on_hold"


def test_default_policy_blocks_obsidian_vault_for_lineage_records(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    (root / ".obsidian").mkdir()
    path = root / "lineage" / "default.jsonl"
    with pytest.raises(StorageSecurityError) as exc:
        require_local_working_store(path, record_class="lineage")
    assert exc.value.decision.reason == "obsidian_vault_on_hold"


def test_default_policy_blocks_common_external_sync_paths(tmp_path: Path) -> None:
    root = tmp_path / "OneDrive" / "Sayane"
    path = root / "review_decisions.jsonl"
    with pytest.raises(StorageSecurityError) as exc:
        require_local_working_store(path, record_class="review_decision")
    assert exc.value.decision.reason == "external_sync_on_hold"


def test_policy_can_explicitly_allow_git_worktree_for_legacy_manual_use(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    path = root / "profiles" / "default" / "candidates.jsonl"
    policy = StorageSecurityPolicy(allow_git_worktree=True)
    decision = require_local_working_store(path, record_class="candidate", policy=policy)
    assert decision.allowed is True


def test_default_policy_is_conservative() -> None:
    policy = default_storage_security_policy()
    assert policy.allow_external_sync is False
    assert policy.allow_git_worktree is False
    assert policy.allow_obsidian_vault is False
