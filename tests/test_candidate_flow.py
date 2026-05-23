import json
import shutil
from pathlib import Path

from omomuki.bridge.config import BridgeConfig
from omomuki.core.loader import load_profile
from omomuki.evaluators.service import approve_candidate, evaluate_candidate
from omomuki.storage.candidates import create_from_capture, load_candidate
from omomuki.storage.lineage_store import list_records


def test_evaluate_and_approve_merges_knowledge(tmp_path: Path) -> None:
    home = tmp_path / "omomuki"
    config = BridgeConfig(home=home)
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "omomuki.profile.yaml",
    )

    candidate = create_from_capture(
        config,
        content="New concept: Resonanceverse portability layer",
        source_type="test",
    )
    evaluated = evaluate_candidate(config, candidate.id)
    assert evaluated.evaluation is not None
    assert evaluated.status == "evaluated"

    approved = approve_candidate(config, candidate.id)
    assert approved.status == "approved"

    profile = load_profile(profile_dir / "omomuki.profile.yaml")
    concepts = profile.knowledge.concepts if profile.knowledge else []
    assert any("Resonanceverse" in c for c in concepts)

    records = list_records(config, "default")
    assert any(r.get("event") == "candidate_approved" for r in records)


def test_legacy_capture_upgraded_on_load(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "omomuki")
    config.candidates_dir.mkdir(parents=True)
    legacy = {
        "id": "legacy1",
        "status": "candidate",
        "content": "Legacy capture line one",
        "source": "selection",
        "captured_at": "2026-05-23T00:00:00+00:00",
    }
    (config.candidates_dir / "legacy1.json").write_text(json.dumps(legacy), encoding="utf-8")
    c = load_candidate(config, "legacy1")
    assert c.kind == "CandidateUpdate"
    assert c.content.startswith("Legacy")
