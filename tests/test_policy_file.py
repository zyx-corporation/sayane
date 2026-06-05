"""T-RDE tests for Custom Policy Files (Phase 15)."""
import tempfile
from pathlib import Path

import yaml

from sayane.core.policy_file import (
    load_and_validate,
    load_policy_file,
    resolve_effective_policy,
    validate_policy_file,
)


def _write_policy(d: dict, suffix: str = ".yaml") -> Path:
    d2 = tempfile.mkdtemp()
    path = Path(d2) / f"policy{suffix}"
    if suffix == ".json":
        import json
        path.write_text(json.dumps(d, indent=2))
    else:
        path.write_text(yaml.safe_dump(d))
    return path


def test_policy_file_validate_accepts_valid_yaml():
    path = _write_policy({
        "schema_version": "sayane-policy-v1",
        "name": "test",
        "extends": "standard",
        "rules": {"bundle_verification": {"signature_unsigned": "warn"}},
    })
    policy, errors = load_and_validate(path)
    assert policy is not None
    assert errors == []


def test_policy_file_validate_accepts_valid_json():
    path = _write_policy({
        "schema_version": "sayane-policy-v1",
        "name": "test-json",
        "extends": "standard",
    }, suffix=".json")
    policy, errors = load_and_validate(path)
    assert policy is not None
    assert errors == []


def test_policy_file_rejects_hard_constraint_override():
    path = _write_policy({
        "schema_version": "sayane-policy-v1",
        "name": "bad",
        "extends": "standard",
        "rules": {"bundle_verification": {"hash_mismatch": "allow"}},
    })
    policy, errors = load_and_validate(path)
    assert any("hash_mismatch" in e for e in errors)


def test_policy_file_rejects_unsafe_auto_approve():
    path = _write_policy({
        "schema_version": "sayane-policy-v1",
        "name": "bad",
        "extends": "standard",
        "rules": {"semantic_review": {"auto_approve": True}},
    })
    policy, errors = load_and_validate(path)
    assert any("auto_approve" in e for e in errors)


def test_policy_file_effective_rules_merge_with_base():
    path = _write_policy({
        "schema_version": "sayane-policy-v1",
        "name": "merged",
        "extends": "strict",
        "rules": {"bundle_verification": {"signature_unsigned": "warn"}},
    })
    policy, errors = load_and_validate(path)
    assert errors == []
    effective = resolve_effective_policy(policy)
    assert effective is not None
    rules = effective["effective_rules"]
    # Inherited: strict blocks hash_missing
    assert rules["bundle_verification"]["hash_missing"] == "block"
    # Overridden: signature_unsigned → warn
    assert rules["bundle_verification"]["signature_unsigned"] == "warn"
    # Hard constraint: hash_mismatch still block
    assert rules["bundle_verification"]["hash_mismatch"] == "block"


def test_invalid_yaml_returns_error():
    d = tempfile.mkdtemp()
    path = Path(d) / "bad.yaml"
    path.write_text("{{invalid: yaml: [")
    policy = load_policy_file(path)
    assert policy is None


def test_missing_extends_rejected():
    path = _write_policy({
        "schema_version": "sayane-policy-v1",
        "name": "bad",
        "extends": "nonexistent",
    })
    policy, errors = load_and_validate(path)
    assert any("extends" in e for e in errors)


def test_invalid_action_value_rejected():
    path = _write_policy({
        "schema_version": "sayane-policy-v1",
        "name": "bad",
        "extends": "standard",
        "rules": {"bundle_verification": {"signature_unsigned": "ignore"}},
    })
    policy, errors = load_and_validate(path)
    assert any("ignore" in e or "allow" in e.lower() for e in errors)
