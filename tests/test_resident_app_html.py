"""Tests for resident app HTML home rendering."""

from pathlib import Path

from sayane.bridge.resident_app_html import render_resident_app_home
from sayane.bridge.resident_app_html import (
    render_resident_app_candidate_detail,
    render_resident_app_candidate_diff,
    render_resident_app_candidate_queue,
    render_resident_app_daemon_panel,
)


def test_render_resident_app_home_includes_bootstrap_and_summary() -> None:
    html = render_resident_app_home(
        {
            "preferred_entrypoint": "/app/overview",
            "read_surfaces": [
                {"path": "/app/overview", "purpose": "primary initial screen payload"},
                {"path": "/app/candidates", "purpose": "reviewable candidate queue"},
            ],
        },
        {
            "summary": {
                "repository_available": True,
                "reviewable_count": 2,
                "approved_context_count": 1,
                "blocked_context_count": 1,
                "daemon_state": "stopped",
                "readiness_status": "review_required",
                "next_action_count": 2,
            },
            "review_summary": {
                "top_items": [
                    {
                        "candidate_id": "cand-001",
                        "status": "pending",
                        "proposal_section": "knowledge.concepts",
                        "display_summary": "Resident app queue item",
                        "requires_review": True,
                    }
                ]
            },
            "daemon_summary": {
                "top_next_actions": [
                    {
                        "kind": "runtime_init",
                        "summary": "Initialize runtime metadata before daemon start",
                    }
                ]
            },
        },
        notice="Clipboard captured.",
    )

    assert "<!DOCTYPE html>" in html
    assert "紗綾音 Resident App Home" in html
    assert "/app/overview" in html
    assert "Resident app queue item" in html
    assert "Initialize runtime metadata before daemon start" in html
    assert "do not patch profile state directly" in html
    assert 'action="/app/ui/capture-clipboard"' in html
    assert 'href="/app/ui/daemon"' in html
    assert "Clipboard captured." in html
    assert 'href="/app/ui/candidates"' in html
    assert 'href="/app/ui/candidates/cand-001"' in html
    assert 'id="resident-app-shell-root"' in html
    assert "/app/ui-state/home" in html
    assert "/app/ui-action/capture-clipboard" in html
    assert "紗綾音 Resident App Shell" in html
    assert "resident-shell-evaluate-form" in html
    assert "resident-shell-approve-form" in html
    assert "resident-shell-reject-form" in html
    assert "resident-shell-revise-form" in html
    assert "Diff Inspection" in html
    assert "Runtime Init Preview" in html
    assert "Cleanup Preview" in html
    assert "Repair Preview" in html
    assert "Service Targets" in html
    assert "LaunchAgent Preview" in html
    assert "LaunchAgent Status" in html
    assert "Daemon Observation" in html
    assert "Quick Links" in html
    assert "Queue Summary" in html
    assert "Current Screen" in html
    assert "Current Target" in html
    assert "JSON Surface" in html
    assert "Detail Summary" in html
    assert "Proposal Summary" in html
    assert "Evaluation Summary" in html
    assert "Lineage Summary" in html
    assert "Lineage Events" in html
    assert "shell-nav-active" in html
    assert "hashchange" in html
    assert "screen=home" in html
    assert "Route State" in html
    assert "Operator Workspace" in html
    assert "Session Actions" in html
    assert "End UI session" in html
    assert "Skip to content" in html


def test_render_resident_app_home_supports_japanese_locale() -> None:
    html = render_resident_app_home(
        {
            "preferred_entrypoint": "/app/overview",
            "read_surfaces": [],
        },
        {
            "summary": {
                "repository_available": True,
                "reviewable_count": 1,
                "approved_context_count": 0,
                "blocked_context_count": 0,
                "daemon_state": "stopped",
                "readiness_status": "review_required",
                "next_action_count": 1,
            },
            "review_summary": {"top_items": []},
            "daemon_summary": {"top_next_actions": []},
        },
        locale="ja",
    )

    assert 'lang="ja"' in html
    assert "ホーム" in html
    assert "<title>紗綾音 Resident App ホーム</title>" in html
    assert "<h1>紗綾音 Resident App ホーム</h1>" in html
    assert "表示言語" in html
    assert "保留候補を作成" in html
    assert 'value="ja"' in html
    assert "概要" in html
    assert "停止中" in html
    assert "知識 / 概念" in html or "レビュー可能な候補はありません。" in html
    assert "紗綾音 Resident App シェル" in html
    assert "操作フォーム" in html
    assert "デーモン観測" in html
    assert "オペレーター作業領域" in html
    assert "セッション操作" in html
    assert "UIセッションを終了" in html
    assert "本文へ移動" in html


def test_render_resident_app_daemon_panel_includes_service_targets_and_launchagent_preview() -> None:
    html = render_resident_app_daemon_panel(
        {
            "status": {"state": "stopped", "is_running_daemon": False, "runtime_initialized": True},
            "readiness": {"readiness_status": "review_required"},
            "runtime_init": {"kind": "resident_daemon_runtime_init_plan", "items": []},
            "cleanup_preview": {"kind": "resident_daemon_cleanup_apply_preview", "decision_report": {"decisions": []}},
            "repair_preview": {"kind": "resident_daemon_repair_apply_preview", "decisions": {}},
            "service_targets_status": {
                "kind": "resident_daemon_service_targets_status",
                "current_platform": "macos",
                "recommended_target": "macos_launchagent",
                "targets": [
                    {
                        "target": "macos_launchagent",
                        "platform": "macos",
                        "service_manager": "launchd",
                        "status": "supported_preview_apply_control",
                    }
                ],
            },
            "launchagent_preview": {
                "kind": "resident_daemon_launchagent_plan",
                "operation_id": "launchagent-123",
                "preview_hash": "abc123",
                "label": "com.sayane.resident.bridge",
                "plist_path": "/tmp/com.sayane.resident.bridge.plist",
                "launchctl_commands": {
                    "bootstrap": "launchctl bootstrap gui/501 /tmp/com.sayane.resident.bridge.plist",
                },
            },
            "launchagent_status": {
                "kind": "resident_daemon_launchagent_status",
                "label": "com.sayane.resident.bridge",
                "plist_path": "/tmp/com.sayane.resident.bridge.plist",
                "plist_exists": True,
                "loaded_status": "loaded",
                "service_manager": "launchd",
            },
            "next_actions": [],
        }
    )

    assert "Service Targets" in html
    assert "LaunchAgent Preview" in html
    assert "LaunchAgent Status" in html
    assert "launchctl bootstrap" in html
    assert "com.sayane.resident.bridge" in html


def test_resident_app_home_translates_read_surface_purposes_in_japanese() -> None:
    html = render_resident_app_home(
        {
            "preferred_entrypoint": "/app/overview",
            "read_surfaces": [
                {"path": "/app/overview", "purpose": "primary initial screen payload"},
                {"path": "/app/candidates", "purpose": "reviewable candidate queue"},
            ],
        },
        {
            "summary": {
                "repository_available": True,
                "reviewable_count": 1,
                "approved_context_count": 0,
                "blocked_context_count": 0,
                "daemon_state": "stopped",
                "readiness_status": "review_required",
                "next_action_count": 1,
            },
            "review_summary": {"top_items": []},
            "daemon_summary": {"top_next_actions": []},
        },
        locale="ja",
    )

    assert "初期画面の主要ペイロード" in html
    assert "レビュー可能な候補キュー" in html


def test_resident_app_japanese_display_values_cover_status_and_source_tokens() -> None:
    html = render_resident_app_home(
        {
            "preferred_entrypoint": "/app/overview",
            "read_surfaces": [],
        },
        {
            "summary": {
                "repository_available": True,
                "reviewable_count": 1,
                "approved_context_count": 0,
                "blocked_context_count": 0,
                "daemon_state": "stopped",
                "readiness_status": "review_required",
                "next_action_count": 1,
            },
            "review_summary": {"top_items": []},
            "daemon_summary": {"top_next_actions": []},
        },
        locale="ja",
    )

    assert "レビュー要" in html
    assert "停止中" in html


def test_resident_app_shell_home_summary_uses_localized_display_values() -> None:
    source = (Path(__file__).resolve().parents[1] / "src/sayane/bridge/resident_app_html.py").read_text()
    assert 'escapeDisplayHtml(card.value)' in source
    assert 'localized_rde_class = rde_class_label(string_value, locale)' in source
    assert '_translate_read_surface_purpose(surface["purpose"], locale)' in source
    assert '"error.candidate_not_evaluated_for_approve": "この候補は評価済み状態ではないため承認できません。"' in source
    assert '"error.ui_session_required": "Resident App UI セッションが必要です。ローカルシェルを開き直してください。"' in source
    assert '"error.transport_unavailable": "Resident AppシェルからBridgeに接続できませんでした。"' in source
    assert '"action.logout": "UIセッションを終了"' in source
    assert '"label.session_actions": "セッション操作"' in source
    assert '"detail.skip_to_content": "本文へ移動"' in source
    assert '"label.diff_summary_cards": "差分要約"' in source
    assert '"title.diff": "紗綾音 候補差分"' in source
    assert '"heading.diff": "候補差分"' in source
    assert '"label.app_shell": "紗綾音 Resident App シェル"' in source
    assert '"heading.queue": "紗綾音 Resident App Candidate Queue"' in source
    assert '"heading.daemon": "紗綾音 Resident App Daemon Panel"' in source
    assert '"label.pending": "保留"' in source
    assert '"label.evaluated": "評価済み"' in source
    assert '"label.diff_payload": "差分ペイロード"' in source
    assert '"action.evaluate": "評価する"' in source
    assert '"action.approve": "承認する"' in source
    assert '"action.reject": "却下する"' in source
    assert '"value.pid_dir": "PID ディレクトリ"' in source
    assert '"value.socket_file": "ソケットファイル"' in source
    assert '"value.no_action": "操作不要"' in source
    assert '"phrase.reason_artifact_missing_no_cleanup": "アーティファクトが存在しないため、クリーンアップは不要です。"' in source
    assert "function localizeData(value)" in source
    assert 'JSON.stringify(localizeData(state.detailDiff), null, 2)' in source
    assert 'JSON.stringify(localizeData(daemon), null, 2)' in source
    assert '"noticePendingCandidateCreated": _copy("notice.pending_candidate_created", locale)' in source
    assert '"authFailure": _copy("error.ui_session_required", locale)' in source
    assert '"transportFailure": _copy("error.transport_unavailable", locale)' in source
    assert '"emptyReviewableCandidates": _copy("empty.reviewable_candidates", locale)' in source
    assert '"logout": _copy("action.logout", locale)' in source
    assert '"sessionActions": _copy("label.session_actions", locale)' in source
    assert '"workspaceDesc": _copy("detail.workspace_desc", locale)' in source
    assert '"logout": "/app/ui-action/session/logout"' in source
    assert 'throw new Error(strings.transportFailure || strings.genericShellFetch || "Request failed.");' in source
    assert 'if (response.status === 401 || response.status === 403) {' in source
    assert 'detail = strings.authFailure || detail;' in source
    assert 'setStatus(strings.noticeCandidateEvaluated, "notice");' in source
    assert 'setStatus(strings.noticeCandidateApproved, "notice");' in source
    assert 'setStatus(strings.noticeCandidateRejected, "notice");' in source
    assert 'setStatus(strings.noticeRevisedCandidateCreated, "notice");' in source
    assert 'state.queueState = {' in source
    assert 'state.daemonState = {' in source
    assert ".skip-link" in source
    assert "@media (max-width: 720px)" in source
    assert 'data-shell-logout' in source
    assert 'role="status" aria-live="polite"' in source
    assert "function logoutSession()" in source


def test_resident_app_english_display_values_are_human_readable() -> None:
    html = render_resident_app_home(
        {
            "preferred_entrypoint": "/app/overview",
            "read_surfaces": [],
        },
        {
            "summary": {
                "repository_available": True,
                "reviewable_count": 1,
                "approved_context_count": 0,
                "blocked_context_count": 0,
                "daemon_state": "stopped",
                "readiness_status": "review_required",
                "next_action_count": 1,
            },
            "review_summary": {"top_items": []},
            "daemon_summary": {"top_next_actions": []},
        },
        locale="en",
    )

    assert "review required" in html
    assert "stopped" in html
    assert "knowledge / concepts" in html or "No reviewable candidates." in html
    assert "Quick Links" in html
    assert "Queue Summary" in html
    assert "Current Screen" in html
    assert "Current Target" in html
    assert "JSON Surface" in html
    assert "Detail Summary" in html
    assert "Proposal Summary" in html
    assert "Evaluation Summary" in html
    assert "Lineage Summary" in html
    assert "Route State" in html
    assert "Role" in html
    assert "Recommendation" in html
    assert "Target" in html


def test_render_resident_app_candidate_queue_links_to_detail() -> None:
    html = render_resident_app_candidate_queue(
        {
            "reviewable_count": 1,
            "status_counts": {"pending": 1},
            "top_sections": [{"section": "knowledge.concepts", "count": 1}],
            "items": [
                {
                    "id": "cand-001",
                    "status": "pending",
                    "section": "knowledge.concepts",
                    "evaluation_level": 1,
                    "rde_class": "Preserved",
                    "content_preview": "Resident queue preview",
                }
            ],
        }
    )

    assert "紗綾音 Resident App Candidate Queue" in html
    assert "/app/ui/candidates/cand-001" in html
    assert "Resident queue preview" in html
    assert "1 / Preserved" in html
    assert "Pending:" in html
    assert "Evaluated:" in html
    assert "Queue Status Counts" in html
    assert "Top Sections" in html
    assert "knowledge / concepts" in html


def test_render_resident_app_candidate_queue_supports_japanese_status_labels() -> None:
    html = render_resident_app_candidate_queue(
        {
            "reviewable_count": 1,
            "status_counts": {"pending": 1, "evaluated": 2},
            "top_sections": [{"section": "knowledge.concepts", "count": 1}],
            "items": [
                {
                    "id": "cand-001",
                    "status": "pending",
                    "section": "knowledge.concepts",
                    "evaluation_level": 1,
                    "rde_class": "Preserved",
                    "content_preview": "Resident queue preview",
                }
            ],
        },
        locale="ja",
    )

    assert "保留:" in html
    assert "評価済み:" in html
    assert "<strong>保留</strong>: 1" in html
    assert "<strong>評価済み</strong>: 2" in html
    assert "1 / 保存された要素" in html


def test_render_resident_app_candidate_diff_supports_japanese_labels() -> None:
    html = render_resident_app_candidate_diff(
        "cand-001",
        {
            "ui_summary": {
                "section": "important_terms",
                "list_operation": "list_add",
                "added_count": 1,
                "already_present_count": 0,
            },
            "add": {"knowledge": {"concepts": ["Resident diff"]}},
        },
        locale="ja",
    )

    assert "候補差分" in html
    assert "差分要約" in html
    assert "差分ペイロード" in html
    assert "重要語" in html
    assert "リスト追加" in html


def test_render_resident_app_candidate_detail_links_to_diff() -> None:
    html = render_resident_app_candidate_detail(
        {
            "id": "cand-001",
            "status": "pending",
            "content": "Detailed resident app text",
            "proposal": {"section": "knowledge.concepts", "operation": "add"},
            "evaluation": {"level": 1, "rde_class": None},
            "source": {"type": "clipboard"},
        },
        diff_path="/app/ui/candidates/cand-001/diff",
        error="Evaluate before approve.",
    )

    assert "Candidate Detail" in html
    assert "Detailed resident app text" in html
    assert "/app/ui/candidates/cand-001/diff" in html
    assert '/app/ui/candidates/cand-001/evaluate' in html
    assert '/app/ui/candidates/cand-001/revise' in html
    assert '/app/ui/candidates/cand-001/approve' in html
    assert '/app/ui/candidates/cand-001/reject' in html
    assert "Evaluate before approve." in html
    assert "Action guidance" in html
    assert "Not evaluated yet" in html
    assert "add" in html
    assert "<dt>Section</dt>" in html
    assert "<dt>Operation</dt>" in html
    assert "<dt>Level</dt>" in html


def test_render_resident_app_candidate_detail_shows_rde_guidance_when_evaluated() -> None:
    html = render_resident_app_candidate_detail(
        {
            "id": "cand-001",
            "status": "evaluated",
            "content": "Evaluated resident app text",
            "proposal": {"section": "knowledge.concepts", "operation": "add"},
            "evaluation": {"level": 1, "rde_class": "Preserved"},
            "source": {"type": "clipboard"},
        },
        diff_path="/app/ui/candidates/cand-001/diff",
    )

    assert "RDE class: Preserved" in html
    assert "pill-evaluated" in html
    assert "Level 1 / Preserved" in html


def test_render_resident_app_candidate_diff_renders_payload() -> None:
    html = render_resident_app_candidate_diff(
        "cand-001",
        {
            "ui_summary": {
                "section": "important_terms",
                "list_operation": "list_add",
                "added_count": 1,
                "already_present_count": 0,
            },
            "add": {"knowledge": {"concepts": ["Resident diff"]}},
        },
    )

    assert "Candidate Diff" in html
    assert "Resident diff" in html
    assert "/app/ui/candidates/cand-001" in html
    assert "Diff Summary" in html
    assert "List Operation" in html
    assert "&quot;knowledge&quot;" in html


def test_render_resident_app_daemon_panel_renders_preview() -> None:
    html = render_resident_app_daemon_panel(
        {
            "status": {
                "state": "stopped",
                "is_running_daemon": False,
                "runtime_initialized": False,
            },
            "readiness": {
                "readiness_status": "review_required",
            },
            "runtime_init": {
                "kind": "resident_daemon_runtime_init_plan",
                "operation_id": "runtime-init-123",
                "plan_fingerprint": "abc123",
                "review_required": True,
                "operator_confirmation_signal": "--apply",
                "metadata_path": "/tmp/run/state/runtime-init.json",
                "items": [
                    {
                        "path_role": "runtime_root",
                        "status": "create",
                        "path": "/tmp/run",
                        "reason": "missing directory may be created with explicit apply intent",
                    }
                ],
            },
            "cleanup_preview": {
                "kind": "resident_daemon_cleanup_apply_preview",
                "operation_id": "cleanup-preview-123",
                "preview_hash": "cleanuphash",
                "allowed_targets": ["pid_file", "lock_file"],
                "decision_report": {
                    "decision_policy": "manual_review_required",
                    "manual_review_required": True,
                    "decisions": [
                        {
                            "artifact_kind": "pid_file",
                            "diagnostic_status": "present_review_required",
                            "recommendation": "manual_review_required",
                            "reason": "artifact is present; ownership and liveness are not proven by preview diagnostics",
                        }
                    ],
                },
            },
            "repair_preview": {
                "kind": "resident_daemon_repair_apply_preview",
                "operation_id": "repair-preview-123",
                "preview_hash": "repairhash",
                "allowed_targets": ["runtime_root"],
                "decisions": {
                    "runtime_root": {
                        "status": "missing",
                        "repairable": True,
                        "path": "/tmp/run",
                    }
                },
            },
            "next_actions": [
                {
                    "command": "sayane app daemon-runtime-init --json",
                    "reason": "Inspect missing runtime directories before any control action.",
                }
            ],
        }
    )

    assert "紗綾音 Resident App Daemon Panel" in html
    assert "stopped" in html
    assert "review required" in html
    assert "sayane app daemon-runtime-init --json" in html
    assert "runtime-init-123" in html
    assert "cleanup-preview-123" in html
    assert "repair-preview-123" in html
    assert "manual review required" in html
    assert "PID file" in html
    assert "runtime root" in html
    assert "does not prove process identity" in html


def test_render_resident_app_candidate_detail_supports_japanese_locale() -> None:
    html = render_resident_app_candidate_detail(
        {
            "id": "cand-001",
            "status": "pending",
            "content": "Detailed resident app text",
            "proposal": {"section": "knowledge.concepts", "operation": "add"},
            "evaluation": {"level": 1, "rde_class": None},
            "source": {"type": "clipboard"},
        },
        diff_path="/app/ui/candidates/cand-001/diff",
        locale="ja",
        error="承認前に評価してください。",
    )

    assert "候補詳細" in html
    assert "<title>紗綾音 候補詳細</title>" in html
    assert "キューへ戻る" in html
    assert "操作ガイダンス" in html
    assert "提案" in html
    assert "評価" in html
    assert "承認前に評価してください。" in html
    assert ">保留<" in html
    assert "<strong>ID:</strong>" in html
    assert "<strong>状態:</strong>" in html
    assert "<strong>セクション:</strong>" in html
    assert "<strong>ソース:</strong>" in html
    assert "<dt>セクション</dt>" in html
    assert "<dt>操作</dt>" in html
    assert "<dt>レベル</dt>" in html
    assert "知識 / 概念" in html
    assert "クリップボード" in html
    assert ">追加<" in html
    assert "保存された要素" in html or "未評価" in html
    assert "レビュー要" in html or "評価済み" in html or "保留" in html


def test_render_resident_app_daemon_panel_supports_japanese_locale() -> None:
    html = render_resident_app_daemon_panel(
        {
            "status": {
                "state": "stopped",
                "is_running_daemon": False,
                "runtime_initialized": False,
            },
            "readiness": {
                "readiness_status": "review_required",
            },
            "runtime_init": {
                "kind": "resident_daemon_runtime_init_plan",
                "items": [
                    {
                        "path_role": "runtime_root",
                        "status": "create",
                        "path": "/tmp/run",
                        "reason": "missing directory may be created with explicit apply intent",
                    }
                ],
            },
            "cleanup_preview": {
                "kind": "resident_daemon_cleanup_apply_preview",
                "decision_report": {
                    "decisions": [
                        {
                            "artifact_kind": "pid_file",
                            "diagnostic_status": "present_review_required",
                            "recommendation": "manual_review_required",
                            "reason": "artifact is present",
                        },
                        {
                            "artifact_kind": "socket_file",
                            "diagnostic_status": "missing",
                            "recommendation": "no_action",
                            "reason": "artifact is missing; no cleanup is needed",
                        }
                    ],
                },
            },
            "repair_preview": {
                "kind": "resident_daemon_repair_apply_preview",
                "decisions": {
                    "runtime_root": {
                        "status": "missing",
                        "repairable": True,
                        "path": "/tmp/run",
                    },
                    "pid_dir": {
                        "status": "missing",
                        "repairable": True,
                        "path": "/tmp/run/pid",
                    }
                },
            },
            "next_actions": [],
        },
        locale="ja",
    )

    assert 'lang="ja"' in html
    assert "<title>紗綾音 Resident App デーモンパネル</title>" in html
    assert "紗綾音 Resident App デーモンパネル" in html
    assert "稼働中" in html
    assert "ランタイム初期化済み" in html
    assert "準備状態" in html
    assert "停止中" in html
    assert "いいえ" in html
    assert "ランタイムルート" in html
    assert "作成" in html
    assert "PID ファイル" in html
    assert "ソケットファイル" in html
    assert "要レビューで存在" in html
    assert "未作成" in html
    assert "操作不要" in html
    assert "PID ディレクトリ" in html
    assert "不足ディレクトリは明示的な適用意図のもとで作成できます" in html
    assert "アーティファクトは存在します" in html
    assert "アーティファクトが存在しないため、クリーンアップは不要です。" in html
    assert "socket_file" not in html
    assert "pid_dir" not in html
    assert "no_action" not in html
    assert ">役割<" in html
    assert ">推奨<" in html
    assert ">対象<" in html
    assert ">修復可能<" in html
