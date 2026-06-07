"""T-RDE tests for Sidepanel Scoped Context Review (F-3)."""
import json
from pathlib import Path


def _load_fixture():
    path = Path(__file__).resolve().parent / "fixtures" / "extension" / "scoped-accept-sidepanel-candidate.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_sidepanel_candidate_card_shows_scoped_accept_badge():
    fx = _load_fixture()
    assert fx["status"] == "scoped_accept"


def test_sidepanel_candidate_card_shows_scope():
    fx = _load_fixture()
    assert fx["accepted_scope"]["level"] == "project"
    assert fx["accepted_scope"]["target"] == "zenn-sayane-series"


def test_sidepanel_detail_shows_conditions():
    fx = _load_fixture()
    assert len(fx["conditions"]) >= 1
    assert "目的に限定" in fx["conditions"][0]


def test_sidepanel_detail_shows_negative_constraints():
    fx = _load_fixture()
    assert len(fx["negative_constraints"]) >= 1
    assert "昇格しない" in fx["negative_constraints"][0]


def test_sidepanel_detail_shows_promotion_policy():
    fx = _load_fixture()
    assert fx["promotion_policy"]["can_promote"] is False
    assert "project_to_global" in fx["promotion_policy"]["requires_review_for"]


def test_promotion_risk_flag_present():
    fx = _load_fixture()
    assert "promotion_risk" in fx["flags"]


def test_reuse_policy_review_on_reuse():
    fx = _load_fixture()
    assert fx["reuse_policy"]["review_on_reuse"] is True


def test_review_show_displays_scoped_accept_metadata():
    from sayane.core.review_decision import ReviewDecision, build_lineage_event

    d = ReviewDecision(
        candidate_id="c-sidepanel",
        decision="scoped_accept",
        reason="Locally useful.",
        accepted_scope={"level": "project", "target": "zenn", "sub_scope": "intro"},
        conditions=["目的限定"],
        negative_constraints=["昇格しない"],
        promotion_policy={"can_promote": False},
    )
    lineage = build_lineage_event(d)
    assert "scoped_accept" in lineage
    assert lineage["scoped_accept"]["accepted_scope"]["target"] == "zenn"
    assert "昇格しない" in lineage["scoped_accept"]["negative_constraints"][0]
