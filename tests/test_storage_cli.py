import json
import re
from pathlib import Path

import yaml
from typer.testing import CliRunner

from sayane.cli.main import app
from sayane.core.export_package import create_package
from sayane.core.bundle_provenance import compute_bundle_hash, generate_bundle_id

runner = CliRunner()


def _plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_storage_index_updates_profile(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner.invoke(app, ["init"])
    ctx = home / ".sayane" / "profiles" / "default" / "context"
    (ctx / "extra.md").write_text("# Extra\n", encoding="utf-8")

    result = runner.invoke(app, ["storage", "index"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "entries:" in result.stdout


def test_storage_import_dry_run(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "from-vault.md").write_text("# V\n", encoding="utf-8")

    runner.invoke(app, ["init"])
    result = runner.invoke(
        app,
        ["storage", "import", str(vault), "--dry-run"],
    )
    assert result.exit_code == 0
    assert "from-vault.md" in result.stdout


def test_storage_import_uses_obsidian_vault_env(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "env-note.md").write_text("# Env\n", encoding="utf-8")
    monkeypatch.setenv("SAYANE_OBSIDIAN_VAULT", str(vault))

    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["storage", "import", "--dry-run"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "env-note.md" in result.stdout


def test_storage_import_requires_legacy_confirmation(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("# N\n", encoding="utf-8")

    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["storage", "import", str(vault)])
    assert result.exit_code != 0
    assert "--legacy-compatible" in _plain(result.stdout + result.stderr)


def test_storage_import_allows_legacy_confirmation(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("# N\n", encoding="utf-8")

    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["storage", "import", str(vault), "--legacy-compatible"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Imported" in result.stdout or "取り込みました" in result.stdout


def test_storage_import_can_scope_to_source_subdir(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    (vault / "safe").mkdir(parents=True)
    (vault / "safe" / "note.md").write_text("# Safe\n", encoding="utf-8")
    (vault / "other").mkdir()
    (vault / "other" / "skip.md").write_text("# Skip\n", encoding="utf-8")

    runner.invoke(app, ["init"])
    result = runner.invoke(
        app,
        [
            "storage",
            "import",
            str(vault),
            "--legacy-compatible",
            "--source-subdir",
            "safe",
        ],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    ctx = home / ".sayane" / "profiles" / "default" / "context"
    assert (ctx / "note.md").exists()
    assert not (ctx / "skip.md").exists()


def test_storage_import_rejects_forbidden_source_subdir(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    vault.mkdir()

    runner.invoke(app, ["init"])
    result = runner.invoke(
        app,
        [
            "storage",
            "import",
            str(vault),
            "--legacy-compatible",
            "--source-subdir",
            ".obsidian",
        ],
    )
    assert result.exit_code != 0
    assert "Forbidden export subdir segment" in (result.stdout + result.stderr)


def test_storage_export_rejects_forbidden_subdir(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    vault.mkdir()

    runner.invoke(app, ["init"])
    result = runner.invoke(
        app,
        [
            "storage",
            "export",
            str(vault),
            "--legacy-compatible",
            "--subdir",
            ".obsidian",
        ],
    )
    assert result.exit_code != 0
    assert "Forbidden export subdir segment" in (result.stdout + result.stderr)


def test_storage_export_package_creates_vault_aware_package(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    runner.invoke(app, ["init"])
    output = tmp_path / "package"
    result = runner.invoke(app, ["storage", "export-package", "--output", str(output)])
    assert result.exit_code == 0, result.stdout + result.stderr
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["package_kind"] == "vault_aware_external_package"
    assert manifest["boundary"]["review_required_before_merge"] is True
    assert manifest["boundary"]["import_contract"] == "preview_only"
    assert manifest["boundary"]["candidate_persistence_allowed"] is False
    assert manifest["boundary"]["retention_expiry_mode"] == "warning_only"
    assert manifest["retention"]["package_class"] == "reviewable_external_exchange"
    artifact_retention_classes = {
        artifact.get("retention", {}).get("retention_class")
        for artifact in manifest["artifacts"]
    }
    assert "reviewable_context_bundle" in artifact_retention_classes
    assert "redacted_audit_export" in artifact_retention_classes
    bundle = yaml.safe_load((output / "artifacts" / "bundle.yml").read_text(encoding="utf-8"))
    assert bundle["metadata"]["external_context"] is True
    assert bundle["metadata"]["retention"]["retention_class"] == "reviewable_context_bundle"
    assert bundle["content_hash"]["bundle_id"].startswith("bundle-sha256-")


def test_storage_import_package_previews_candidates_without_mutation(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner.invoke(app, ["init"])

    package_dir = tmp_path / "package"
    bundle_path = tmp_path / "bundle.yml"
    payload = {
        "metadata": {
            "source": "sayane_vault_aware_package",
            "llm_memory": False,
            "external_context": True,
        },
        "knowledge": {
            "concepts": ["package preview concept"]
        },
    }
    content_hash = compute_bundle_hash(payload)
    payload["content_hash"] = {
        "algorithm": "sha256",
        "value": content_hash,
        "bundle_id": generate_bundle_id(content_hash),
    }
    bundle_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    create_package(
        package_dir,
        {"bundle": bundle_path},
        package_kind="vault_aware_external_package",
        purpose="reviewable_external_exchange",
        boundary={
            "storage_boundary": "vault_aware_external_package",
            "canonical_profile_state": False,
            "review_required_before_merge": True,
            "legacy_compatibility_path": False,
        },
        policy_profile="vault-aware-external",
    )

    result = runner.invoke(app, ["storage", "import-package", str(package_dir)])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "candidate" in result.stdout.lower()
    profile_path = home / ".sayane" / "profiles" / "default" / "sayane.profile.yaml"
    assert "package preview concept" not in profile_path.read_text(encoding="utf-8")


def test_storage_queue_package_persists_candidates_without_profile_mutation(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner.invoke(app, ["init"])

    package_dir = tmp_path / "package"
    bundle_path = tmp_path / "bundle.yml"
    payload = {
        "metadata": {
            "source": "sayane_vault_aware_package",
            "llm_memory": False,
            "external_context": True,
        },
        "knowledge": {
            "concepts": ["queued package concept"]
        },
    }
    content_hash = compute_bundle_hash(payload)
    payload["content_hash"] = {
        "algorithm": "sha256",
        "value": content_hash,
        "bundle_id": generate_bundle_id(content_hash),
    }
    bundle_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    create_package(
        package_dir,
        {"bundle": bundle_path},
        package_kind="vault_aware_external_package",
        purpose="reviewable_external_exchange",
        policy_profile="vault-aware-external",
    )

    result = runner.invoke(app, ["storage", "queue-package", str(package_dir)])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Queued" in result.stdout or "review queue" in result.stdout or "追加しました" in result.stdout
    candidates = sorted((home / ".sayane" / "candidates").glob("*.json"))
    assert candidates
    stored = json.loads(candidates[0].read_text(encoding="utf-8"))
    assert stored["status"] == "pending"
    assert stored["target_profile_id"] == "default"
    profile_path = home / ".sayane" / "profiles" / "default" / "sayane.profile.yaml"
    assert "queued package concept" not in profile_path.read_text(encoding="utf-8")
