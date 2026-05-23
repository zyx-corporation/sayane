import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from omomuki.bridge.config import BridgeConfig
from omomuki.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from omomuki.core.loader import load_profile
from omomuki.evaluators.merge import merge_candidate_into_profile
from omomuki.evaluators.service import approve_candidate
from omomuki.storage.candidates import save_candidate


def _candidate(section: str, items: list[str]) -> CandidateUpdate:
    return CandidateUpdate(
        id="c-test",
        content="test",
        source=CandidateSource(type="test", captured_at=datetime.now(UTC)),
        proposal=CandidateProposal(section=section, add=items),
    )


def test_merge_values_requires_force(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    candidate = _candidate("values.core", ["test value"])
    with pytest.raises(ValueError, match="force-critical"):
        merge_candidate_into_profile(profile, candidate)


def test_merge_values_with_force(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    candidate = _candidate("values.core", ["test value"])
    updated = merge_candidate_into_profile(profile, candidate, force_critical=True)
    assert "test value" in updated.values.core


def test_approve_critical_via_cli_flow(tmp_path: Path) -> None:
    home = tmp_path / "omomuki"
    config = BridgeConfig(home=home)
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "omomuki.profile.yaml",
    )
    candidate = CandidateUpdate(
        id="c-voice",
        content="tone: collaborative",
        source=CandidateSource(type="test", captured_at=datetime.now(UTC)),
        proposal=CandidateProposal(section="voice.tone", add=["collaborative"]),
        status="evaluated",
    )
    save_candidate(config, candidate)
    approved = approve_candidate(config, candidate.id, force_critical=True)
    assert approved.status == "approved"
    profile = load_profile(profile_dir / "omomuki.profile.yaml")
    assert "collaborative" in profile.voice.tone
