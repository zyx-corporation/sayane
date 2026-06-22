"""Tests for resident app contract payload."""

from __future__ import annotations

from sayane.app import build_app_contract


def test_app_contract_exposes_entrypoint_and_surfaces() -> None:
    payload = build_app_contract()

    assert payload["kind"] == "resident_app_contract"
    assert payload["contract_version"] == "1"
    assert payload["preferred_entrypoint"] == "/app/overview"
    assert any(
        surface["path"] == "/app/ui"
        for surface in payload["human_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui/candidates"
        for surface in payload["human_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui/capture-clipboard"
        for surface in payload["human_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui/daemon"
        for surface in payload["human_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui-state/*"
        for surface in payload["human_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui-action/*"
        for surface in payload["human_surfaces"]
    )
    assert any(
        surface["path"] == "/app/overview"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "/app/screen-state/home"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "cli:sayane app daemon-packaging-status --json"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "cli:sayane app daemon-service-targets-status --json"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "cli:sayane app daemon-service-control-boundary --json"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "cli:sayane app daemon-supervision-status --json"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "cli:sayane app daemon-launchagent-preview --json"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "cli:sayane app daemon-recovery-consent-status --json"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui-state/home"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui-state/candidates/{id}/lineage"
        for surface in payload["read_surfaces"]
    )
    assert any(
        surface["path"] == "/app/capture-clipboard"
        for surface in payload["write_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui-action/candidates/{id}/approve"
        for surface in payload["write_surfaces"]
    )
    assert any(
        surface["path"] == "/app/ui-action/session/logout"
        for surface in payload["write_surfaces"]
    )
    assert any(
        contract["screen"] == "home"
        for contract in payload["screen_state_contracts"]
    )
    assert "GET /app/overview" in payload["recommended_flow"]
    assert "GET /app/ui-state/home" in payload["recommended_flow"]
    assert "POST /app/ui-action/candidates/{id}/approve or /reject" in payload["recommended_flow"]
    assert "POST /app/ui-action/session/logout" in payload["recommended_flow"]


def test_app_contract_uses_local_shell_wording_for_cookie_backed_ui_surfaces() -> None:
    payload = build_app_contract()

    purposes = [
        *(surface["purpose"] for surface in payload["human_surfaces"]),
        *(surface["purpose"] for surface in payload["read_surfaces"]),
    ]
    assert any("Bridge-hosted local shell" in purpose for purpose in purposes)
    assert all("Bridge-hosted app shell" not in purpose for purpose in purposes)


def test_app_contract_exposes_explicit_non_mvp_boundary_matrix() -> None:
    payload = build_app_contract()

    boundaries = {
        item["topic"]: item
        for item in payload["non_mvp_boundaries"]
    }

    assert boundaries["daemon_identity_proof"]["status"] == "explicit_defer"
    assert boundaries["daemon_readiness_and_api_readiness_proof"]["status"] == "explicit_defer"
    assert boundaries["os_service_integration_ui"]["status"] == "separate_plan"
    assert boundaries["tray_or_background_supervision_ui"]["status"] == "separate_plan"
    assert boundaries["direct_profile_patch_ui"]["status"] == "explicit_defer"
    assert any(
        doc.endswith("resident-app-ui-integration-contract.md")
        for doc in boundaries["direct_profile_patch_ui"]["governing_docs"]
    )
    assert any(
        doc.endswith("v1.0.15-operator-packaging-supervision-phase-plan.md")
        for doc in boundaries["os_service_integration_ui"]["governing_docs"]
    )


def test_app_contract_exposes_surface_roles_and_shared_semantics() -> None:
    payload = build_app_contract()

    surface_roles = {
        item["surface"]: item
        for item in payload["surface_roles"]
    }
    shared_semantics = {
        item["topic"]: item
        for item in payload["shared_semantics"]
    }

    assert surface_roles["resident_app"]["role"] == "primary_growth_surface"
    assert surface_roles["extension"]["role"] == "compatibility_surface"
    assert shared_semantics["app_facing_endpoint_contracts"]["shared_by_design"] is True
    assert shared_semantics["screen_state_payload_semantics"]["shared_by_design"] is True
    assert shared_semantics["review_and_daemon_boundary_wording"]["shared_by_design"] is True
    assert shared_semantics["host_container_ux"]["shared_by_design"] is False
    assert shared_semantics["auth_session_handling"]["shared_by_design"] is False
    assert any(
        item["command"] == "sayane app daemon-packaging-status --json"
        for item in payload["operator_cli_surfaces"]
    )
    assert any(
        item["command"] == "sayane app daemon-service-targets-status --json"
        for item in payload["operator_cli_surfaces"]
    )
    assert any(
        item["command"] == "sayane app daemon-service-control-boundary --json"
        for item in payload["operator_cli_surfaces"]
    )
    assert any(
        item["command"] == "sayane app daemon-supervision-status --json"
        for item in payload["operator_cli_surfaces"]
    )
    assert any(
        item["command"] == "sayane app daemon-launchagent-preview --json"
        for item in payload["operator_cli_surfaces"]
    )
    assert any(
        item["command"] == "sayane app daemon-recovery-consent-status --json"
        for item in payload["operator_cli_surfaces"]
    )
