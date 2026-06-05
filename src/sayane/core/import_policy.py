"""Import Policy Profiles (Phase 11).

Policy profiles define how verification results and semantic review
flags are handled. Strict/standard/legacy-compatible/development
profiles determine whether to allow, warn, or block imports.

No policy auto-approves or auto-rejects candidates.
Hash mismatch and invalid signature always block.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PolicyAction = Literal["allow", "warn", "block"]
PolicyName = Literal["strict", "standard", "legacy_compatible", "development"]


@dataclass
class PolicyDecision:
    code: str
    severity: PolicyAction
    message: str


@dataclass
class PolicyResult:
    profile: str
    status: str  # "PASS" | "WARN" | "BLOCK"
    import_allowed: bool
    review_allowed: bool
    apply_allowed: bool
    decisions: list[PolicyDecision] = field(default_factory=list)


# --- Built-in policy profiles ---

BUILTIN_POLICIES: dict[str, dict] = {
    "strict": {
        "name": "strict",
        "description": "CI, production, pre-approval verification. Blocks unverified bundles and semantic warnings.",
        "bundle_verification": {
            "hash_missing": "block",
            "hash_mismatch": "block",
            "metadata_missing": "block",
            "signature_unsigned": "warn",
            "signature_invalid": "block",
        },
        "semantic_review": {
            "review_required": "block",
            "semantic_overlap": "block",
            "unstable_placement": "block",
            "boundary_sensitive": "block",
        },
        "audit": {
            "audit_store_unwritable": "block",
            "missing_audit_source_binding": "block",
            "missing_decision_reason": "block",
        },
        "transfer_report": {
            "fail_on_warnings": True,
            "unverified_bundle": "block",
            "critical_regression": "block",
        },
    },
    "standard": {
        "name": "standard",
        "description": "Normal operations. Warns on missing hash/metadata but blocks boundary violations.",
        "bundle_verification": {
            "hash_missing": "warn",
            "hash_mismatch": "block",
            "metadata_missing": "warn",
            "signature_unsigned": "allow",
            "signature_invalid": "block",
        },
        "semantic_review": {
            "review_required": "warn",
            "semantic_overlap": "warn",
            "unstable_placement": "warn",
            "boundary_sensitive": "block",
        },
        "audit": {
            "audit_store_unwritable": "block",
            "missing_audit_source_binding": "warn",
            "missing_decision_reason": "block",
        },
        "transfer_report": {
            "fail_on_warnings": False,
            "unverified_bundle": "warn",
            "critical_regression": "block",
        },
    },
    "legacy_compatible": {
        "name": "legacy_compatible",
        "description": "Backward compatible with old fixtures. Warns broadly but blocks critical failures.",
        "bundle_verification": {
            "hash_missing": "warn",
            "hash_mismatch": "block",
            "metadata_missing": "warn",
            "signature_unsigned": "allow",
            "signature_invalid": "block",
        },
        "semantic_review": {
            "review_required": "warn",
            "semantic_overlap": "warn",
            "unstable_placement": "warn",
            "boundary_sensitive": "warn",
        },
        "audit": {
            "audit_store_unwritable": "block",
            "missing_audit_source_binding": "warn",
            "missing_decision_reason": "block",
        },
        "transfer_report": {
            "fail_on_warnings": False,
            "unverified_bundle": "warn",
            "critical_regression": "block",
        },
    },
    "development": {
        "name": "development",
        "description": "Local development. Allows missing metadata but blocks hash mismatch and invalid signatures.",
        "bundle_verification": {
            "hash_missing": "allow",
            "hash_mismatch": "block",
            "metadata_missing": "allow",
            "signature_unsigned": "allow",
            "signature_invalid": "block",
        },
        "semantic_review": {
            "review_required": "warn",
            "semantic_overlap": "warn",
            "unstable_placement": "warn",
            "boundary_sensitive": "warn",
        },
        "audit": {
            "audit_store_unwritable": "block",
            "missing_audit_source_binding": "warn",
            "missing_decision_reason": "block",
        },
        "transfer_report": {
            "fail_on_warnings": False,
            "unverified_bundle": "warn",
            "critical_regression": "block",
        },
    },
}

DEFAULT_POLICY: PolicyName = "standard"

# Hard constraints — override all policies
_HARD_BLOCK_CODES: frozenset[str] = frozenset({
    "hash_mismatch",
    "signature_invalid",
    "audit_store_unwritable",
})


# --- Policy evaluation engine ---


def evaluate_policy(
    policy_name: str,
    verification_status: str = "verified",  # verified | unverified | failed
    verification_details: str = "",
    semantic_flags: list[str] | None = None,
    audit_writable: bool = True,
    audit_source_bound: bool = True,
) -> PolicyResult:
    """Evaluate a policy against verification and semantic review results."""
    profile = BUILTIN_POLICIES.get(policy_name)
    if profile is None:
        return PolicyResult(
            profile=policy_name,
            status="BLOCK",
            import_allowed=False,
            review_allowed=False,
            apply_allowed=False,
            decisions=[PolicyDecision(code="unknown_policy", severity="block", message=f"Unknown policy: {policy_name}")],
        )

    decisions: list[PolicyDecision] = []
    semantic_flags = semantic_flags or []

    # Bundle verification
    bv = profile["bundle_verification"]
    if verification_status == "unverified":
        action = bv.get("hash_missing", "warn")
    elif verification_status == "failed":
        action = "block"  # hash_mismatch always blocks
    else:
        action = "allow"

    if action != "allow":
        decisions.append(PolicyDecision(
            code="hash_missing" if verification_status == "unverified" else "hash_mismatch",
            severity=action,
            message=verification_details or f"Bundle hash status: {verification_status}",
        ))

    # Semantic review flags → policy decisions
    sr = profile["semantic_review"]
    flag_map = {
        "review_required": "review_required",
        "semantic_overlap": "semantic_overlap",
        "unstable_placement": "unstable_placement",
        "boundary_sensitive": "boundary_sensitive",
    }
    for flag in semantic_flags:
        code = flag_map.get(flag, flag)
        action = sr.get(code, "warn")
        if action != "allow":
            decisions.append(PolicyDecision(
                code=code,
                severity=action,
                message=f"Semantic flag: {flag}",
            ))

    # Audit constraints
    audit_policy = profile["audit"]
    if not audit_writable:
        decisions.append(PolicyDecision(
            code="audit_store_unwritable",
            severity="block",  # always block
            message="Audit store is not writable.",
        ))
    if not audit_source_bound:
        action = audit_policy.get("missing_audit_source_binding", "warn")
        decisions.append(PolicyDecision(
            code="missing_audit_source_binding",
            severity=action,
            message="Audit record missing source bundle binding.",
        ))

    # Apply hard constraints
    for d in decisions:
        if d.code in _HARD_BLOCK_CODES:
            d.severity = "block"

    # Compute overall status
    has_block = any(d.severity == "block" for d in decisions)
    has_warn = any(d.severity == "warn" for d in decisions)

    if has_block:
        status = "BLOCK"
    elif has_warn:
        status = "WARN"
    else:
        status = "PASS"

    return PolicyResult(
        profile=policy_name,
        status=status,
        import_allowed=not has_block,
        review_allowed=True,  # human review always allowed
        apply_allowed=not has_block,
        decisions=decisions,
    )


def list_policies() -> list[str]:
    return sorted(BUILTIN_POLICIES.keys())


def get_policy(policy_name: str) -> dict | None:
    return BUILTIN_POLICIES.get(policy_name)
