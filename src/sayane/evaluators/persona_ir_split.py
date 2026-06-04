"""Split structured persona YAML into section-specific IR Candidates."""

from __future__ import annotations

from typing import Any

from sayane.core.candidate import (
    CandidateProposal,
    CandidateStoragePolicy,
    CandidateUpdate,
)


# --- Field mapping: persona YAML path → IR section + storage policy ---

_PERSONA_FIELD_MAP: list[dict[str, Any]] = [
    {
        "target_path": "identity.name",
        "yaml_keys": [
            "preferred_name",
            "casual_name",
            "formal_name",
            "external_japanese_name",
            "name",
        ],
        "display_key": "detail.ir_section.identity_name",
        "policy": CandidateStoragePolicy(
            storage_kind="profile_ir",
            target_path="identity.name",
            prompt_export="default",
            sensitivity="internal",
        ),
    },
    {
        "target_path": "identity.contact",
        "yaml_keys": ["email"],
        "display_key": "detail.ir_section.identity_contact",
        "policy": CandidateStoragePolicy(
            storage_kind="profile_ir",
            target_path="identity.contact",
            prompt_export="never",
            sensitivity="private",
        ),
    },
    {
        "target_path": "identity.role",
        "yaml_keys": ["role", "position"],
        "display_key": "detail.ir_section.identity_role",
        "policy": CandidateStoragePolicy(
            storage_kind="profile_ir",
            target_path="identity.role",
            prompt_export="on_demand",
            sensitivity="internal",
        ),
    },
    {
        "target_path": "organization.profile",
        "yaml_keys": ["organization.name", "organization.focus", "organization"],
        "display_key": "detail.ir_section.organization_profile",
        "policy": CandidateStoragePolicy(
            storage_kind="profile_ir",
            target_path="organization.profile",
            prompt_export="on_demand",
            sensitivity="internal",
        ),
    },
    {
        "target_path": "interaction.language",
        "yaml_keys": [
            "language.default",
            "language.secondary",
            "language",
            "default_language",
        ],
        "display_key": "detail.ir_section.interaction_language",
        "policy": CandidateStoragePolicy(
            storage_kind="profile_ir",
            target_path="interaction.language",
            prompt_export="default",
            sensitivity="internal",
        ),
    },
    {
        "target_path": "interaction.response_style",
        "yaml_keys": ["language.response_style", "response_style"],
        "display_key": "detail.ir_section.interaction_response_style",
        "policy": CandidateStoragePolicy(
            storage_kind="profile_ir",
            target_path="interaction.response_style",
            prompt_export="default",
            sensitivity="internal",
        ),
    },
    {
        "target_path": "technical_preferences.development",
        "yaml_keys": ["development_preferences", "technical_preferences"],
        "display_key": "detail.ir_section.technical_preferences",
        "policy": CandidateStoragePolicy(
            storage_kind="profile_ir",
            target_path="technical_preferences.development",
            prompt_export="on_demand",
            sensitivity="internal",
        ),
    },
    {
        "target_path": "writing_profile",
        "yaml_keys": ["writing_preferences", "writing_profile"],
        "display_key": "detail.ir_section.writing_profile",
        "policy": CandidateStoragePolicy(
            storage_kind="profile_ir",
            target_path="writing_profile",
            prompt_export="on_demand",
            sensitivity="internal",
        ),
    },
]


def _get_nested(parsed: dict[str, Any], key: str) -> Any:
    """Drill into parsed YAML dict by dot-separated path."""
    value: Any = parsed
    for part in key.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _resolve_persona_root(parsed: dict[str, Any]) -> dict[str, Any] | None:
    """If the parsed YAML has a top-level 'persona' key, unwrap it."""
    if "persona" in parsed and isinstance(parsed["persona"], dict):
        return parsed["persona"]
    return parsed


class IrCandidateDraft:
    """Intermediate representation of a single IR candidate before saving."""

    def __init__(
        self,
        target_path: str,
        display_key: str,
        values: dict[str, str],
        policy: CandidateStoragePolicy,
        proposal_section: str = "knowledge.concepts",
    ) -> None:
        self.target_path = target_path
        self.display_key = display_key
        self.values = values
        self.policy = policy
        self.proposal_section = proposal_section

    def content_preview(self) -> str:
        return "\n".join(f"{k}: {v}" for k, v in self.values.items())

    def display_summary(self, locale: str | None = None) -> str:
        ja = bool(locale and str(locale).lower().startswith("ja"))
        name = self.target_path
        prefix = f"[{name}] " if ja else f"[{name}] "
        return prefix + self.content_preview()


def split_persona_to_ir_candidates(
    parsed: dict[str, Any],
) -> list[IrCandidateDraft]:
    """Parse a persona YAML dict and produce IR candidate drafts for each section.

    Only sections with at least one non-empty value are included.
    """
    root = _resolve_persona_root(parsed)
    if root is None:
        return []

    drafts: list[IrCandidateDraft] = []
    for mapping in _PERSONA_FIELD_MAP:
        values: dict[str, str] = {}
        for yaml_key in mapping["yaml_keys"]:
            raw = _get_nested(root, yaml_key)
            if raw is None:
                # Also try at top level (for non-nested persona roots)
                raw = _get_nested(parsed, yaml_key)
            if raw is None:
                continue
            # Handle dict values (e.g., language: { default: ja, secondary: en })
            if isinstance(raw, dict):
                for sub_key, sub_val in raw.items():
                    if isinstance(sub_val, str) and sub_val.strip():
                        values[f"{yaml_key}.{sub_key}"] = sub_val.strip()
            elif isinstance(raw, str) and raw.strip():
                values[yaml_key] = raw.strip()
            elif isinstance(raw, list):
                values[yaml_key] = ", ".join(str(v) for v in raw if str(v).strip())

        if not values:
            continue

        section = mapping.get("proposal_section", "knowledge.concepts")
        draft = IrCandidateDraft(
            target_path=mapping["target_path"],
            display_key=mapping["display_key"],
            values=values,
            policy=mapping["policy"],
            proposal_section=section,
        )
        drafts.append(draft)

    return drafts


def build_ir_proposal(draft: IrCandidateDraft) -> CandidateProposal:
    """Build a CandidateProposal from an IR candidate draft."""
    items: list[dict[str, str]] = [
        {"section": draft.proposal_section, "name": k, "value": v, "yaml_path": draft.target_path}
        for k, v in draft.values.items()
    ]
    return CandidateProposal(
        section=draft.proposal_section,
        operation="ir_split",
        add=[],
        items=items,
        already_present=[],
        summary=draft.display_summary(),
    )


def storage_policy_for_target_path(target_path: str) -> CandidateStoragePolicy | None:
    """Look up the storage policy for a given IR target path."""
    for mapping in _PERSONA_FIELD_MAP:
        if mapping["target_path"] == target_path:
            return mapping["policy"]
    return None


def detect_structured_persona_document(parsed_yaml: dict[str, Any]) -> bool:
    """Check whether the parsed YAML contains a recognizable structured persona."""
    root = _resolve_persona_root(parsed_yaml)
    if root is None or not isinstance(root, dict):
        return False
    # Check for at least 2 recognizable persona keys across our field map
    matched = 0
    for mapping in _PERSONA_FIELD_MAP:
        for yaml_key in mapping["yaml_keys"]:
            if _get_nested(root, yaml_key) is not None:
                matched += 1
                break
        if matched >= 2:
            return True
    return False
