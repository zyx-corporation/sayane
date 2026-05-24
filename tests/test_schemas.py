import json
from pathlib import Path

import jsonschema
import yaml


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_schema(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def test_minimal_profile_matches_schema(schemas_dir: Path, examples_dir: Path) -> None:
    schema = _load_schema(schemas_dir / "sayane-profile.schema.json")
    profile = _load_yaml(examples_dir / "profiles" / "minimal.yaml")
    jsonschema.validate(instance=profile, schema=schema)


def test_schema_files_are_valid_json(schemas_dir: Path) -> None:
    for name in ("sayane-profile.schema.json", "prompt-ir.schema.json"):
        schema = _load_schema(schemas_dir / name)
        assert "$schema" in schema
        assert "title" in schema
