"""Tests for Local Vault diagnostic CLI."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from sayane.cli.app import build_app


def test_vault_status_default_reports_no_production_backend() -> None:
    result = CliRunner().invoke(build_app(), ["vault", "status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "unavailable"
    assert payload["requested_mode"] == "production"
    assert payload["production_ready"] is False


def test_vault_status_test_mode_requires_explicit_flag() -> None:
    result = CliRunner().invoke(build_app(), ["vault", "status", "--test", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "available"
    assert payload["requested_mode"] == "test"
    assert payload["runtime_mode"] == "test"
    assert payload["vault_mode"] == "test"
    assert payload["keychain_assurance"] == "test_only"
    assert payload["test_only"] is True
    assert payload["production_ready"] is False
    assert payload["repositories"] == ["candidate", "review_decision", "lineage"]


def test_vault_policy_lists_all_presets() -> None:
    result = CliRunner().invoke(build_app(), ["vault", "policy", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    levels = [item["level"] for item in payload["policies"]]
    assert levels == ["normal", "sensitive", "deep_private"]


def test_vault_policy_can_show_sensitive_preset() -> None:
    result = CliRunner().invoke(
        build_app(),
        ["vault", "policy", "--level", "sensitive", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["level"] == "sensitive"
    assert payload["idle_timeout_seconds"] == 5 * 60
    assert payload["absolute_timeout_seconds"] == 15 * 60
    assert "candidate:write" in payload["scopes"]
    assert "review_decision:write" in payload["scopes"]
    assert "lineage:write" in payload["scopes"]
    assert "deep_private:read" not in payload["scopes"]
