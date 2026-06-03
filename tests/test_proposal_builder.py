from pathlib import Path

from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.rde import classify_rde
from sayane.core.loader import load_profile
from sayane.core.models import CommunicationMode, MajorProject


def test_project_like_capture_builds_structured_items() -> None:
    content = """
major_projects:
  - name: "Kotone"
    summary: "宅内・エッジAI、PoP UID、個体管理、音声UI、Home Assistant統合"
  - name: "Kotonoha"
    summary: "AI協働・生成的監査・文脈継承基盤"
"""
    proposal = build_proposal_from_content(content)
    assert proposal.operation == "add_or_update"
    assert proposal.section == "major_projects"
    assert proposal.items
    assert proposal.add == []
    assert proposal.items[0]["name"] == "Kotone"
    assert proposal.summary == content.strip()


def test_project_like_capture_is_marked_as_suspicious_drift_when_section_is_wrong() -> None:
    content = """
major_projects:
  - name: "Sayane"
    summary: "local-first LLM context store / bridge / MCP server 構想"
"""
    proposal = build_proposal_from_content(content, section="knowledge.concepts")
    rde_class, notes = classify_rde(content, proposal)
    assert rde_class == "Suspicious Drift"
    assert any(n.key == "potential_redundancy_with_major_projects" for n in notes)


def test_project_duplicates_become_noop_and_preserved() -> None:
    content = """
major_projects:
  - name: "Kotone"
    summary: "宅内・エッジAI、PoP UID、個体管理、音声UI、Home Assistant統合"
  - name: "Kotonoha"
    summary: "AI協働・生成的監査・文脈継承基盤"
"""
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    profile.major_projects = [
        MajorProject(
            name="Kotone",
            summary="宅内・エッジAI、PoP UID、個体管理、音声UI、Home Assistant統合",
        ),
        MajorProject(name="Kotonoha", summary="AI協働・生成的監査・文脈継承基盤"),
    ]
    proposal = build_proposal_from_content(content, profile=profile)
    assert proposal.section == "major_projects"
    assert proposal.operation == "no_op_or_duplicate"
    assert proposal.items == []
    assert len(proposal.already_present) == 2
    assert proposal.add == []
    rde_class, notes = classify_rde(content, proposal)
    assert rde_class == "Preserved"
    assert any(n.key == "no_effective_profile_update_major_projects" for n in notes)


def test_communication_mode_capture_infers_structured_section() -> None:
    content = """
communication_mode:
  assistant_name_for_chatgpt: "ココリア"
  preferred_address: "tomyukさん"
  intimate_address: "ともゆきさん"
  collaboration_style:
    - "一緒に考える"
    - "複数選択肢を提示する"
"""
    proposal = build_proposal_from_content(content)
    assert proposal.section == "communication_mode"
    assert proposal.operation == "add_or_update"
    assert proposal.add == []
    assert any(
        item["path"] == "communication_mode.assistant_name_for_chatgpt"
        and item["value"] == "ココリア"
        for item in proposal.items
    )
    assert any(
        item["path"] == "communication_mode.preferred_address"
        and item["value"] == "tomyukさん"
        for item in proposal.items
    )


def test_communication_mode_duplicates_become_noop_and_not_extension() -> None:
    content = """
communication_mode:
  assistant_name_for_chatgpt: "ココリア"
  preferred_address: "tomyukさん"
  intimate_address: "ともゆきさん"
  collaboration_style:
    - "一緒に考える"
"""
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    profile.communication_mode = CommunicationMode(
        assistant_name_for_chatgpt="ココリア",
        preferred_address="tomyukさん",
        intimate_address="ともゆきさん",
        collaboration_style=["一緒に考える"],
    )
    proposal = build_proposal_from_content(content, profile=profile)
    assert proposal.section == "communication_mode"
    assert proposal.operation == "no_op_or_duplicate"
    assert proposal.items == []
    assert proposal.already_present
    assert proposal.add == []
    rde_class, _notes = classify_rde(content, proposal)
    assert rde_class == "Preserved"


def test_communication_mode_misclassified_to_knowledge_is_unresolved_gap() -> None:
    content = """
communication_mode:
  assistant_name_for_chatgpt: "ココリア"
"""
    proposal = build_proposal_from_content(content, section="knowledge.concepts")
    assert proposal.items
    rde_class, _notes = classify_rde(content, proposal)
    assert rde_class == "Unresolved Gap"
