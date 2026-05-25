"""L1 acceptance tests for CLI / Bridge-adjacent flows (#92).

Maps to docs/cli-acceptance-test.md and docs/acceptance-spec.md L1 backlog items.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sayane.bridge.config import BridgeConfig
from sayane.cli.app import build_app
from sayane.cli.i18n import set_locale
from sayane.cli.main import app
from sayane.core.loader import load_profile
from sayane.storage.candidates import create_from_capture, load_candidate

runner = CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture
def default_profile(isolated_home: Path) -> tuple[BridgeConfig, Path]:
    config = BridgeConfig(home=isolated_home / ".sayane")
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    profile_path = profile_dir / "sayane.profile.yaml"
    shutil.copy(Path("examples/profiles/minimal.yaml"), profile_path)
    return config, profile_path


def _candidate_id(config: BridgeConfig) -> str:
    return next(config.candidates_dir.glob("*.json")).stem


# --- CLI error paths (ERR-01, ERR-02) ---


def test_compile_unknown_target(examples_dir: Path) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    result = runner.invoke(
        app,
        ["compile", "--target", "not-a-llm", "--profile", str(profile_path)],
    )
    assert result.exit_code != 0
    assert "Unknown target" in (result.stdout + result.stderr + str(result.exception))


def test_compile_missing_profile() -> None:
    missing = Path("/no/such/sayane.profile.yaml")
    result = runner.invoke(
        app,
        ["compile", "--target", "chatgpt", "--profile", str(missing)],
    )
    assert result.exit_code != 0
    assert "not found" in (result.stdout + result.stderr + str(result.exception)).lower()


# --- Candidate full flow (CAND / CLI-07) ---


def test_candidate_show_diff_approve_reject_lineage(
    default_profile: tuple[BridgeConfig, Path],
) -> None:
    config, profile_path = default_profile
    cid = create_from_capture(config, "acceptance concept one", "test").id

    show = runner.invoke(app, ["candidate", "show", cid])
    assert show.exit_code == 0
    assert cid in show.stdout
    assert "knowledge" in show.stdout or "proposal" in show.stdout

    evaluate = runner.invoke(app, ["candidate", "evaluate", cid])
    assert evaluate.exit_code == 0
    assert "rde_class" in evaluate.stdout

    diff = runner.invoke(app, ["candidate", "diff", cid])
    assert diff.exit_code == 0
    assert "add" in diff.stdout

    before = load_profile(profile_path)
    concepts_before = list(before.knowledge.concepts if before.knowledge else [])

    approve = runner.invoke(app, ["candidate", "approve", cid])
    assert approve.exit_code == 0
    assert "acceptance concept one" in approve.stdout or cid in approve.stdout

    after = load_profile(profile_path)
    concepts_after = list(after.knowledge.concepts if after.knowledge else [])
    assert len(concepts_after) >= len(concepts_before)

    lineage = runner.invoke(app, ["candidate", "lineage"])
    assert lineage.exit_code == 0
    assert "candidate_approved" in lineage.stdout

    cid2 = create_from_capture(config, "reject me please", "test").id
    runner.invoke(app, ["candidate", "evaluate", cid2])
    reject = runner.invoke(app, ["candidate", "reject", cid2, "--reason", "test reject"])
    assert reject.exit_code == 0
    assert load_candidate(config, cid2).status == "rejected"


def test_candidate_approve_critical_without_force_rejected(
    default_profile: tuple[BridgeConfig, Path],
) -> None:
    config, profile_path = default_profile
    cid = create_from_capture(config, "values.core: must change core values", "test").id
    runner.invoke(app, ["candidate", "evaluate", cid])

    profile = load_profile(profile_path)
    core_before = list(profile.values.core)

    result = runner.invoke(app, ["candidate", "approve", cid])
    assert result.exit_code != 0
    assert "force-critical" in (result.stdout + result.stderr + str(result.exception)).lower()

    profile_after = load_profile(profile_path)
    assert list(profile_after.values.core) == core_before


def test_sec02_profile_not_merged_before_approve(
    default_profile: tuple[BridgeConfig, Path],
) -> None:
    config, profile_path = default_profile
    marker = "SEC02-unique-marker-xyz"
    cid = create_from_capture(config, f"New concept: {marker}", "test").id
    runner.invoke(app, ["candidate", "evaluate", cid])

    profile = load_profile(profile_path)
    concepts = profile.knowledge.concepts if profile.knowledge else []
    assert not any(marker in c for c in concepts)

    runner.invoke(app, ["candidate", "approve", cid])
    profile_merged = load_profile(profile_path)
    concepts_after = profile_merged.knowledge.concepts if profile_merged.knowledge else []
    assert any(marker in c for c in concepts_after)


# --- Storage CLI (STOR / CLI-10) ---


def test_storage_export_and_commit(isolated_home: Path) -> None:
    init = runner.invoke(app, ["init"])
    assert init.exit_code == 0

    vault = isolated_home / "vault"
    vault.mkdir()
    ctx = isolated_home / ".sayane" / "profiles" / "default" / "context"
    (ctx / "export-me.md").write_text("# Export\n", encoding="utf-8")

    export = runner.invoke(app, ["storage", "export", str(vault)])
    assert export.exit_code == 0
    assert (vault / "sayane" / "export-me.md").exists()

    commit = runner.invoke(
        app,
        ["storage", "commit", "-m", "acceptance test commit"],
    )
    assert commit.exit_code == 0
    assert "Committed" in commit.stdout or "committed" in commit.stdout.lower()


def test_storage_backend_set_cli(isolated_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["init"])
    monkeypatch.setattr("sayane.storage.factory.sayane_home", lambda: isolated_home / ".sayane")

    result = runner.invoke(app, ["storage", "backend", "set", "filesystem"])
    assert result.exit_code == 0
    assert "filesystem" in result.stdout


# --- MCP CLI (MCP-01, MCP-02) ---


def test_mcp_context_packet_cli(default_profile: tuple[BridgeConfig, Path]) -> None:
    del default_profile
    result = runner.invoke(
        app,
        ["mcp", "context-packet", "--target", "claude", "--profile-id", "default"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["format"] == "anthropic_messages"
    assert "messages" in data["payload"] or "system" in str(data["payload"])


# --- i18n (CLI-12) ---


def test_cli_lang_flag_overrides_sayane_lang(
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAYANE_LANG", "ja")
    set_locale("en")
    result = runner.invoke(build_app(), ["--lang", "en", "candidate", "list"])
    assert result.exit_code == 0
    assert "No candidates" in result.stdout
    set_locale("en")


def test_cli_sayane_lang_ja_messages(
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAYANE_LANG", "ja")
    set_locale("ja")
    result = runner.invoke(build_app(), ["candidate", "list"])
    assert result.exit_code == 0
    assert "Candidate がありません" in result.stdout
    set_locale("en")


# --- Plugin boundary PLG-01 ---


def test_help_excludes_commercial_commands_without_extensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sayane.cli.plugins.register_cli_extensions",
        lambda _app: None,
    )
    set_locale("en")
    oss_app = build_app()
    result = runner.invoke(oss_app, ["--help"])
    assert result.exit_code == 0
    for commercial in ("license", "confidentiality", "daemon"):
        assert commercial not in result.stdout.split("Commands")[1]
