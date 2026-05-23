from datetime import datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from omomuki.core.loader import load_profile
from omomuki.core.models import OmomukiProfile, PromptIR


def test_load_minimal_example_profile(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    assert profile.kind == "OmomukiProfile"
    assert profile.identity.name == "Example User"
    assert profile.identity.preferred_name == "example"
    assert "RDE" in profile.knowledge.concepts


def test_profile_rejects_wrong_kind(examples_dir: Path) -> None:
    data = yaml.safe_load((examples_dir / "profiles" / "minimal.yaml").read_text(encoding="utf-8"))
    data["kind"] = "WrongKind"
    with pytest.raises(ValidationError):
        OmomukiProfile.model_validate(data)


def test_prompt_ir_rejects_wrong_kind() -> None:
    with pytest.raises(ValidationError):
        PromptIR.model_validate(
            {
                "version": "0.1.0",
                "kind": "WrongKind",
                "system": [],
                "context": [],
                "instruction": [],
                "constraints": [],
                "examples": [],
            }
        )


def test_lineage_parses_iso_datetime(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    assert isinstance(profile.lineage.created_at, datetime)
