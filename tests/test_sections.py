from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.sections import infer_proposal_section


def test_infer_values_section() -> None:
    assert infer_proposal_section("values.core: curiosity") == "values.core"


def test_build_proposal_for_policy_avoid() -> None:
    p = build_proposal_from_content("policy.response.avoid\n- overclaiming")
    assert p.section == "policy.response.avoid"
    assert p.add


def test_kotone_project_does_not_match_voice_tone() -> None:
    content = "- Melotone: Edge AI / Home Automation\n"
    assert infer_proposal_section(content) == "knowledge.concepts"


def test_tone_yaml_key_matches_voice_tone() -> None:
    content = "voice:\n  tone:\n    - collaborative\n"
    assert infer_proposal_section(content) == "voice.tone"


def test_organization_roles_matches_identity_roles() -> None:
    content = "organization:\n  roles:\n    - architect\n"
    assert infer_proposal_section(content) == "identity.roles"


def test_structured_persona_defaults_to_knowledge() -> None:
    content = (
        "person:\n  name:\n    formal_ja: Example\n"
        "projects:\n  melotone:\n    name_en: Melotone\n"
        "organization:\n  roles:\n    - lead\n"
    )
    assert infer_proposal_section(content) == "knowledge.concepts"


def test_hardcore_values_not_values_core() -> None:
    assert infer_proposal_section("hardcore values in gaming") == "knowledge.concepts"
