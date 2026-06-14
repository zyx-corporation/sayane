"""Registry of acceptance scenario IDs covered by L1 pytest (#92)."""

from __future__ import annotations

import importlib

import pytest

# scenario_id -> "module.path::function_name"
ACCEPTANCE_L1_COVERAGE: dict[str, str] = {
    "ERR-01": "tests.test_acceptance_cli::test_compile_unknown_target",
    "ERR-02": "tests.test_acceptance_cli::test_compile_missing_profile",
    "CAND-flow": "tests.test_acceptance_cli::test_candidate_show_diff_approve_reject_lineage",
    "CAND-critical": (
        "tests.test_acceptance_cli::test_candidate_approve_critical_without_force_rejected"
    ),
    "SEC-02": "tests.test_acceptance_cli::test_sec02_profile_not_merged_before_approve",
    "STOR-export-commit": "tests.test_acceptance_cli::test_storage_export_and_commit",
    "STOR-backend-set": "tests.test_acceptance_cli::test_storage_backend_set_cli",
    "MCP-context-packet": "tests.test_acceptance_cli::test_mcp_context_packet_cli",
    "CLI-12": "tests.test_acceptance_cli::test_cli_lang_flag_overrides_sayane_lang",
    "CLI-12b": "tests.test_acceptance_cli::test_cli_sayane_lang_ja_messages",
    "PLG-01": (
        "tests.test_acceptance_cli::test_help_excludes_commercial_commands_without_extensions"
    ),
    "BRG-reject": "tests.test_bridge_api::test_candidate_reject",
    "BRG-critical": "tests.test_bridge_api::test_candidate_critical_approve_requires_force",
}


def _import_test_module(nodeid: str):
    """Import a test module by its package-qualified pytest node id."""
    module_name, func_name = nodeid.split("::")
    return importlib.import_module(module_name), func_name


@pytest.mark.parametrize("scenario_id,nodeid", sorted(ACCEPTANCE_L1_COVERAGE.items()))
def test_acceptance_scenario_has_pytest(scenario_id: str, nodeid: str) -> None:
    module, func_name = _import_test_module(nodeid)
    assert hasattr(module, func_name), f"{scenario_id}: missing {func_name} in {module.__name__}"
