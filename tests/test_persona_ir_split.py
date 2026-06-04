"""Tests for persona IR split (#124)."""
import pytest

from sayane.evaluators.persona_ir_split import (
    detect_structured_persona_document,
    split_persona_to_ir_candidates,
    storage_policy_for_target_path,
)

SAMPLE_PERSONA = {
    "persona": {
        "preferred_name": "Taro",
        "casual_name": "Taro",
        "email": "taro@example.com",
        "role": "engineer",
        "language": {
            "default": "ja",
            "secondary": "en",
            "response_style": "precise and logical",
        },
        "development_preferences": {
            "editor": "vim",
            "os": "linux",
        },
    },
}


def test_detect_structured_persona():
    assert detect_structured_persona_document(SAMPLE_PERSONA) is True
    assert detect_structured_persona_document({"foo": "bar"}) is False


def test_split_generates_identity_name():
    drafts = split_persona_to_ir_candidates(SAMPLE_PERSONA)
    identity_name = next(d for d in drafts if d.target_path == "identity.name")
    assert "preferred_name" in identity_name.values
    assert identity_name.values["preferred_name"] == "Taro"


def test_split_generates_identity_contact():
    drafts = split_persona_to_ir_candidates(SAMPLE_PERSONA)
    contact = next(d for d in drafts if d.target_path == "identity.contact")
    assert contact.values["email"] == "taro@example.com"
    assert contact.policy.prompt_export == "never"
    assert contact.policy.sensitivity == "private"


def test_split_generates_identity_role():
    drafts = split_persona_to_ir_candidates(SAMPLE_PERSONA)
    role = next(d for d in drafts if d.target_path == "identity.role")
    assert role.values["role"] == "engineer"


def test_split_generates_interaction_response_style():
    drafts = split_persona_to_ir_candidates(SAMPLE_PERSONA)
    style = next(d for d in drafts if d.target_path == "interaction.response_style")
    assert "language.response_style" in style.values
    assert style.policy.prompt_export == "default"


def test_split_generates_technical_preferences():
    drafts = split_persona_to_ir_candidates(SAMPLE_PERSONA)
    tech = next(d for d in drafts if d.target_path == "technical_preferences.development")
    assert tech.policy.prompt_export == "on_demand"


def test_storage_policy_for_target_path():
    policy = storage_policy_for_target_path("identity.contact")
    assert policy is not None
    assert policy.prompt_export == "never"
    assert policy.sensitivity == "private"


def test_empty_persona_returns_no_drafts():
    drafts = split_persona_to_ir_candidates({})
    assert drafts == []


def test_non_persona_not_detected():
    assert detect_structured_persona_document(
        {"important_terms": ["RDE", "Sayane"]},
    ) is False
