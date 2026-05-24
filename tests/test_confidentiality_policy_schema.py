"""JSON Schema contract for SayaneConfidentialityPolicy (#66)."""

import json
from pathlib import Path

import jsonschema
import pytest
import yaml


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_schema(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _level_ids(policy: dict) -> set[str]:
    return {level["id"] for level in policy["classification_levels"]}


def _assert_referenced_levels(policy: dict) -> None:
    ids = _level_ids(policy)
    assert policy["profile_ceiling"] in ids
    for section, level_id in policy["section_limits"].items():
        assert level_id in ids, f"section_limits.{section} references unknown level {level_id!r}"
    for path, level_id in policy.get("context_classifications", {}).items():
        assert level_id in ids, f"context_classifications[{path!r}] references unknown level"


def test_default_policy_matches_schema(schemas_dir: Path, examples_dir: Path) -> None:
    schema = _load_schema(schemas_dir / "sayane-confidentiality-policy.schema.json")
    policy = _load_yaml(examples_dir / "confidentiality" / "default.policy.yaml")
    jsonschema.validate(instance=policy, schema=schema)
    _assert_referenced_levels(policy)


def test_confidentiality_schema_is_valid_json(schemas_dir: Path) -> None:
    schema = _load_schema(schemas_dir / "sayane-confidentiality-policy.schema.json")
    assert schema["title"] == "SayaneConfidentialityPolicy"
    assert schema["properties"]["kind"]["const"] == "SayaneConfidentialityPolicy"


def test_rejects_wrong_kind(schemas_dir: Path, examples_dir: Path) -> None:
    schema = _load_schema(schemas_dir / "sayane-confidentiality-policy.schema.json")
    policy = _load_yaml(examples_dir / "confidentiality" / "default.policy.yaml")
    policy["kind"] = "OtherPolicy"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=policy, schema=schema)


def test_rejects_unknown_rule_action(schemas_dir: Path, examples_dir: Path) -> None:
    schema = _load_schema(schemas_dir / "sayane-confidentiality-policy.schema.json")
    policy = _load_yaml(examples_dir / "confidentiality" / "default.policy.yaml")
    policy["rules"][0]["action"] = "block"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=policy, schema=schema)


def test_classification_level_ids_are_unique(examples_dir: Path) -> None:
    policy = _load_yaml(examples_dir / "confidentiality" / "default.policy.yaml")
    ids = [level["id"] for level in policy["classification_levels"]]
    assert len(ids) == len(set(ids))
