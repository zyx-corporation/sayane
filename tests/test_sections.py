from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.sections import infer_proposal_section


def test_infer_values_section() -> None:
    assert infer_proposal_section("values.core: curiosity") == "values.core"


def test_build_proposal_for_policy_avoid() -> None:
    p = build_proposal_from_content("policy.response.avoid\n- overclaiming")
    assert p.section == "policy.response.avoid"
    assert p.add
