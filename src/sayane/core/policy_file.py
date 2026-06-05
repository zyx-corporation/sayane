"""Custom Policy Files (Phase 15).

Loads YAML/JSON policy files, validates against built-in profiles,
merges overrides, enforces hard constraints.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sayane.core.import_policy import BUILTIN_POLICIES

# --- Hard constraints — cannot be overridden ---

HARD_BLOCK_RULES: dict[str, frozenset[str]] = {
    "bundle_verification": frozenset({"hash_mismatch", "signature_invalid"}),
    "audit": frozenset({"audit_store_unwritable"}),
}

FORBIDDEN_RULE_KEYS: frozenset[str] = frozenset({
    "auto_approve", "auto_reject", "auto_fix", "retry", "ignore",
})

ALLOWED_ACTIONS: frozenset[str] = frozenset({"allow", "warn", "block"})


# --- Policy loader ---

def load_policy_file(path: Path) -> dict[str, Any] | None:
    """Load and parse a policy file (YAML or JSON). Returns None on parse error."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return None


def validate_policy_file(policy: dict[str, Any]) -> list[str]:
    """Validate a policy file dict. Returns list of errors (empty = valid)."""
    errors: list[str] = []

    # Required fields
    if policy.get("schema_version") != "sayane-policy-v1":
        errors.append("schema_version must be 'sayane-policy-v1'")
    if not policy.get("name"):
        errors.append("name is required")
    extends = policy.get("extends")
    if extends not in BUILTIN_POLICIES:
        errors.append(f"extends must be one of: {', '.join(sorted(BUILTIN_POLICIES.keys()))}")

    if extends not in BUILTIN_POLICIES:
        return errors

    base = BUILTIN_POLICIES[extends]
    rules = policy.get("rules", {})

    # Validate rule categories
    for category, overrides in rules.items():
        if not isinstance(overrides, dict):
            errors.append(f"rules.{category} must be a mapping")
            continue

        for key, value in overrides.items():
            # Check forbidden keys
            if key in FORBIDDEN_RULE_KEYS:
                errors.append(f"rules.{category}.{key} is not allowed (auto actions are forbidden)")
                continue

            # Check hard constraints
            if category in HARD_BLOCK_RULES and key in HARD_BLOCK_RULES[category]:
                if value != "block":
                    errors.append(f"rules.{category}.{key} must always be 'block' (hard constraint)")

            # Check valid actions
            if isinstance(value, str):
                if value not in ALLOWED_ACTIONS:
                    errors.append(f"rules.{category}.{key} must be one of: {', '.join(sorted(ALLOWED_ACTIONS))}")

    return errors


def resolve_effective_policy(policy: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve a policy file into an effective policy dict."""
    extends = policy.get("extends")
    base = BUILTIN_POLICIES.get(extends)
    if base is None:
        return None

    import copy
    effective: dict[str, Any] = {
        "name": policy.get("name", extends),
        "extends": extends,
        "effective_rules": copy.deepcopy(base),
    }

    rules = policy.get("rules", {})
    for category, overrides in rules.items():
        if not isinstance(overrides, dict):
            continue
        target = effective["effective_rules"].get(category)
        if target is None:
            continue
        for key, value in overrides.items():
            if key in FORBIDDEN_RULE_KEYS:
                continue
            if category in HARD_BLOCK_RULES and key in HARD_BLOCK_RULES[category]:
                continue  # hard constraint, unchanged
            if isinstance(target, dict):
                target[key] = value

    return effective


def load_and_validate(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load and validate a policy file. Returns (policy_dict, errors)."""
    policy = load_policy_file(path)
    if policy is None:
        return None, ["Could not parse policy file"]
    errors = validate_policy_file(policy)
    return policy, errors
