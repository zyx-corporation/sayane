import json
import shutil
from pathlib import Path

import pytest

from sayane.bridge.config import BridgeConfig
from sayane.mcp.operations import McpOperations


@pytest.fixture
def mcp_ops(tmp_path: Path) -> McpOperations:
    home = tmp_path / "sayane"
    config = BridgeConfig(home=home)
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )
    candidates = config.candidates_dir
    candidates.mkdir(parents=True)
    (candidates / "abc123.json").write_text(
        json.dumps(
            {
                "id": "abc123",
                "status": "candidate",
                "content": "Captured note",
                "source": "test",
                "captured_at": "2026-05-23T00:00:00+00:00",
            },
        ),
        encoding="utf-8",
    )
    return McpOperations(config=config)


def test_list_profiles(mcp_ops: McpOperations) -> None:
    profiles = mcp_ops.list_profiles()
    assert len(profiles) == 1
    assert profiles[0]["id"] == "default"


def test_inspect_profile_summary(mcp_ops: McpOperations) -> None:
    summary = mcp_ops.inspect_profile("default")
    assert summary["identity"]["name"] == "Example User"
    assert summary["read_only"] is True
    assert summary["values_count"] == 2


def test_compile_prompt_chatgpt(mcp_ops: McpOperations) -> None:
    result = mcp_ops.compile_prompt("chatgpt", profile_id="default")
    assert result["target"] == "chatgpt"
    assert "messages" in result["payload"]


def test_generate_context_packet_matches_compile(mcp_ops: McpOperations) -> None:
    a = mcp_ops.compile_prompt("claude", profile_id="default", instruction="Plan tasks")
    b = mcp_ops.generate_context_packet("claude", profile_id="default", instruction="Plan tasks")
    assert a == b


def test_list_candidate_updates(mcp_ops: McpOperations) -> None:
    items = mcp_ops.list_candidate_updates()
    assert len(items) == 1
    assert items[0]["id"] == "abc123"
    assert "Captured" in items[0]["content_preview"]


def test_compile_prompt_gemini(mcp_ops: McpOperations) -> None:
    result = mcp_ops.compile_prompt("gemini", profile_id="default")
    assert result["target"] == "gemini"
    assert "contents" in result["payload"]


def test_compile_prompt_local_openwebui(mcp_ops: McpOperations) -> None:
    result = mcp_ops.compile_prompt("local-openwebui", profile_id="default")
    assert result["target"] == "local-openwebui"
    assert result["format"] == "openai_chat"
    assert "messages" in result["payload"]


def test_unsupported_target(mcp_ops: McpOperations) -> None:
    with pytest.raises(ValueError, match="Unsupported target"):
        mcp_ops.compile_prompt("local-custom")


def test_mcp_candidate_evaluate_and_diff(mcp_ops: McpOperations) -> None:
    evaluated = mcp_ops.evaluate_candidate("abc123", level=1)
    assert evaluated["status"] == "evaluated"
    assert evaluated["evaluation"]["rde_class"]

    diff = mcp_ops.diff_candidate("abc123")
    assert diff["candidate_id"] == "abc123"


def test_mcp_show_candidate(mcp_ops: McpOperations) -> None:
    detail = mcp_ops.show_candidate("abc123")
    assert detail["id"] == "abc123"
    assert "Captured" in detail["content"]
