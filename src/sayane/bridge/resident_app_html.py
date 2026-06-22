"""Server-rendered resident app HTML screens."""

from __future__ import annotations

from html import escape
import json
from typing import Any

from sayane.core.note_display import rde_class_label

DEFAULT_BOOTSTRAP_LOCALE = "en"
SUPPORTED_BOOTSTRAP_LOCALES = ("ja", "en")

BOOTSTRAP_COPY_CORE: dict[str, str] = {
    "nav.home": "Home",
    "nav.candidates": "Candidates",
    "nav.daemon": "Daemon",
    "empty.metadata": "No metadata.",
    "empty.runtime_init_items": "No runtime init items.",
    "empty.cleanup_decisions": "No cleanup decisions.",
    "empty.repair_decisions": "No repair decisions.",
    "empty.reviewable_candidates": "No reviewable candidates.",
    "empty.immediate_daemon_actions": "No immediate daemon actions.",
    "empty.queue_status_summary": "No queue status summary.",
    "empty.section_summary": "No section summary.",
    "empty.structured_diff_summary": "No structured diff summary.",
    "title.home": "紗綾音 Resident App Home",
    "title.queue": "紗綾音 Resident App Queue",
    "title.detail": "紗綾音 Candidate Detail",
    "title.diff": "紗綾音 Candidate Diff",
    "title.daemon": "紗綾音 Resident App Daemon Panel",
    "heading.home": "紗綾音 Resident App Home",
    "heading.queue": "紗綾音 Resident App Candidate Queue",
    "heading.detail": "Candidate Detail",
    "heading.diff": "Candidate Diff",
    "heading.daemon": "紗綾音 Resident App Daemon Panel",
    "desc.home": "Local bridge bootstrap screen for the resident app. Presentation-only, not final GUI framework.",
    "desc.queue": "Reviewable candidates from the app-facing queue. Presentation-only review surface.",
    "desc.diff": "Diff is an approval review aid, not direct profile mutation.",
    "desc.daemon": "Daemon panel is a preview-oriented observation surface. It does not prove process identity, daemon readiness, or API readiness.",
    "desc.boundary": "App-facing writes do not patch profile state directly. Daemon surfaces remain preview-oriented and do not prove process identity, daemon readiness, or API readiness.",
    "desc.detail_boundary": "Candidate review remains inside the existing review/approval boundary.",
}

BOOTSTRAP_COPY_ACTIONS: dict[str, str] = {
    "action.open_daemon_panel": "Open daemon panel",
    "action.create_pending_candidate": "Create pending candidate",
    "action.back_to_queue": "Back to queue",
    "action.open_diff": "Open diff",
    "action.back_to_detail": "Back to detail",
    "action.back_to_home": "Back to home",
    "action.evaluate": "Evaluate",
    "action.approve": "Approve",
    "action.reject": "Reject",
    "action.create_revised_candidate": "Create revised candidate",
    "action.refresh": "Refresh",
    "action.open_app_shell": "Open app shell",
    "action.open_legacy_page": "Open legacy page",
    "action.show_queue": "Show queue",
    "action.show_daemon": "Show daemon",
    "action.show_home": "Show home",
    "action.logout": "End UI session",
}

BOOTSTRAP_COPY_LABELS: dict[str, str] = {
    "label.repository": "Repository",
    "label.reviewable": "Reviewable",
    "label.approved_context": "Approved Context",
    "label.blocked_context": "Blocked Context",
    "label.daemon_state": "Daemon State",
    "label.next_actions": "Next Actions",
    "label.top_review_items": "Top Review Items",
    "label.daemon_next_actions": "Daemon Next Actions",
    "label.bootstrap_contract": "Bootstrap Contract",
    "label.clipboard_capture": "Clipboard Capture",
    "label.overview": "Overview",
    "label.queue_status_counts": "Queue Status Counts",
    "label.top_sections": "Top Sections",
    "label.reviewable_count": "Reviewable count",
    "label.pending": "Pending",
    "label.evaluated": "Evaluated",
    "label.evaluation_summary": "Evaluation Summary",
    "label.operation": "Operation",
    "label.content": "Content",
    "label.actions": "Actions",
    "label.diff_summary": "Diff Summary",
    "label.diff_payload": "Diff Payload",
    "label.runtime_init_preview": "Runtime Init Preview",
    "label.cleanup_preview": "Cleanup Preview",
    "label.repair_preview": "Repair Preview",
    "label.service_targets": "Service Targets",
    "label.launchagent_preview": "LaunchAgent Preview",
    "label.launchagent_status": "LaunchAgent Status",
    "label.packaging_status": "Packaging Status",
    "label.service_control_boundary": "Service Control Boundary",
    "label.supervision_status": "Supervision Status",
    "label.recovery_consent_status": "Recovery and Consent",
    "label.allowed_commands": "Allowed Commands",
    "label.deferred_commands": "Deferred Commands",
    "label.recommended_flow": "Recommended Flow",
    "label.planned_paths": "Planned Paths",
    "label.cleanup_decisions": "Cleanup Decisions",
    "label.repair_decisions": "Repair Decisions",
    "label.status": "Status",
    "label.section": "Section",
    "label.source": "Source",
    "label.running": "Running",
    "label.runtime_initialized": "Runtime Initialized",
    "label.readiness": "Readiness",
    "label.preferred_entrypoint": "Preferred entrypoint",
    "label.locale": "Locale",
    "label.content_field": "Content",
    "label.evaluate_level": "Evaluate level",
    "label.override_reason": "Override reason",
    "label.reject_reason": "Reject reason",
    "label.revised_content": "Revised content",
    "label.target_section": "Target section",
    "label.change_reason": "Change reason",
    "label.force_critical_approve": "Force critical approve",
    "label.diff_summary_missing": "No structured diff summary.",
    "label.app_shell": "紗綾音 Resident App Shell",
    "label.lineage": "Lineage",
    "label.capture_result": "Capture Result",
    "label.legacy_surfaces": "Legacy Surfaces",
    "label.action_forms": "Action Forms",
    "label.diff_inspection": "Diff Inspection",
    "label.preview_metadata": "Preview Metadata",
    "label.daemon_observation": "Daemon Observation",
    "label.quick_links": "Quick Links",
    "label.queue_summary": "Queue Summary",
    "label.reviewable_count_short": "Reviewable Count",
    "label.status_counts_short": "Status Counts",
    "label.top_sections_short": "Top Sections",
    "label.current_screen": "Current Screen",
    "label.current_target": "Current Target",
    "label.json_surface": "JSON Surface",
    "label.detail_summary": "Detail Summary",
    "label.diff_summary_cards": "Diff Summary",
    "label.lineage_summary": "Lineage Summary",
    "label.lineage_events": "Lineage Events",
    "label.proposal_summary": "Proposal Summary",
    "label.evaluation_summary_cards": "Evaluation Summary",
    "label.route_state": "Route State",
    "label.operator_workspace": "Operator Workspace",
    "label.primary_navigation": "Primary Navigation",
    "label.session_actions": "Session Actions",
    "label.shell_workspace": "Shell Workspace",
}

BOOTSTRAP_COPY_DETAILS: dict[str, str] = {
    "detail.home_reviewable": "Pending or evaluated candidates",
    "detail.home_approved_context": "Included in MCP preview",
    "detail.home_blocked_context": "Excluded from MCP preview",
    "detail.home_next_actions": "Top daemon follow-ups",
    "detail.repository_available": "available",
    "detail.repository_unavailable": "unavailable",
    "detail.readiness_prefix": "Readiness",
    "detail.not_evaluated_yet": "Not evaluated yet",
    "detail.not_evaluated_short": "not_evaluated",
    "detail.action_guidance": "Action guidance",
    "detail.action_guidance_pending": "Evaluate this candidate before approval. Approval remains gated by the existing review boundary.",
    "detail.rde_evaluated": "Evaluated",
    "detail.rde_class_prefix": "RDE class",
    "detail.level_prefix": "Level",
    "placeholder.clipboard": "Paste clipboard text here",
    "mapping.proposal": "Proposal",
    "mapping.evaluation": "Evaluation",
    "detail.app_shell_desc": "Interactive local shell backed by UI-session JSON endpoints. Legacy HTML pages remain available as fallback.",
    "detail.loading": "Loading…",
    "detail.empty_lineage": "No lineage events.",
    "detail.capture_hint": "Create a pending candidate from clipboard text, then continue review inside this local shell.",
    "detail.detail_unavailable": "Candidate detail is unavailable.",
    "detail.fallback_queue_error": "Candidate detail refresh failed. Returned to queue.",
    "detail.enter_reject_reason": "Enter reject reason",
    "detail.enter_override_reason": "Enter override reason (optional)",
    "detail.enter_change_reason": "Enter change reason (optional)",
    "detail.enter_target_section": "Enter target section (optional)",
    "detail.enter_revised_content": "Edit candidate content",
    "detail.action_unavailable": "This action is unavailable in the current candidate state.",
    "detail.empty_next_actions": "No immediate daemon actions.",
    "detail.empty_preview": "No preview payload.",
    "detail.empty_service_targets": "No service target entries.",
    "detail.empty_launchagent_preview": "No LaunchAgent preview is available on this platform.",
    "detail.empty_launchagent_status": "No LaunchAgent status is available on this platform.",
    "detail.empty_review_items": "No review items.",
    "detail.empty_quick_links": "No quick links.",
    "detail.target_none": "No active target.",
    "detail.empty_diff_summary": "No diff summary.",
    "detail.route_ready": "Shell route is synchronized.",
    "detail.skip_to_content": "Skip to content",
    "detail.workspace_desc": "Summary-first resident workflow for queue, review, capture, and daemon observation.",
    "detail.session_action_hint": "Use logout to invalidate this browser session without rotating the Bridge bearer.",
}

BOOTSTRAP_COPY_TABLES: dict[str, str] = {
    "table.id": "ID",
    "table.status": "Status",
    "table.section": "Section",
    "table.evaluation": "Evaluation",
    "table.preview": "Preview",
    "table.role": "Role",
    "table.path": "Path",
    "table.reason": "Reason",
    "table.artifact": "Artifact",
    "table.recommendation": "Recommendation",
    "table.target": "Target",
    "table.repairable": "Repairable",
    "boundary.label": "Boundary",
}

BOOTSTRAP_COPY_FIELDS: dict[str, str] = {
    "field.id": "ID",
    "field.kind": "Kind",
    "field.operation_id": "Operation ID",
    "field.plan_fingerprint": "Plan Fingerprint",
    "field.review_required": "Review Required",
    "field.operator_confirmation_signal": "Operator Confirmation",
    "field.metadata_path": "Metadata Path",
    "field.preview_hash": "Preview Hash",
    "field.allowed_targets": "Allowed Targets",
    "field.decision_policy": "Decision Policy",
    "field.manual_review_required": "Manual Review Required",
    "field.section": "Section",
    "field.operation": "Operation",
    "field.level": "Level",
    "field.status": "Status",
    "field.source": "Source",
    "field.source_type": "Source",
    "field.capture_id": "Capture ID",
    "field.decision": "Decision",
    "field.rde_class": "RDE Class",
    "field.events": "Events",
    "field.path_role": "Role",
    "field.path": "Path",
    "field.reason": "Reason",
    "field.artifact_kind": "Artifact",
    "field.diagnostic_status": "Status",
    "field.recommendation": "Recommendation",
    "field.target": "Target",
    "field.repairable": "Repairable",
    "field.evaluation_level": "Evaluation Level",
    "field.added_count": "Added Count",
    "field.already_present_count": "Already Present Count",
    "field.list_operation": "List Operation",
}

BOOTSTRAP_COPY_VALUES: dict[str, str] = {
    "value.true": "true",
    "value.false": "false",
    "value.pending": "pending",
    "value.evaluated": "evaluated",
    "value.approved": "approved",
    "value.rejected": "rejected",
    "value.stopped": "stopped",
    "value.readiness_not_ready": "not ready",
    "value.review_required": "review required",
    "value.manual_review_required": "manual review required",
    "value.present_review_required": "present and requires review",
    "value.action": "action",
    "value.create": "create",
    "value.missing": "missing",
    "value.runtime_init": "runtime init",
    "value.runtime_root": "runtime root",
    "value.pid_dir": "pid directory",
    "value.lock_dir": "lock directory",
    "value.socket_dir": "socket directory",
    "value.log_dir": "log directory",
    "value.temp_dir": "temp directory",
    "value.state_dir": "state directory",
    "value.pid_file": "PID file",
    "value.lock_file": "lock file",
    "value.socket_file": "socket file",
    "value.available": "available",
    "value.unavailable": "unavailable",
    "value.clipboard": "clipboard",
    "value.selection": "selection",
    "value.page": "page",
    "value.manual": "manual",
    "value.knowledge.concepts": "knowledge / concepts",
    "value.important_terms": "important terms",
    "value.add": "add",
    "value.list_add": "list add",
    "value.no_action": "no action",
    "value.resident_daemon_runtime_init_plan": "resident daemon runtime init plan",
    "value.resident_daemon_cleanup_apply_preview": "resident daemon cleanup apply preview",
    "value.resident_daemon_repair_apply_preview": "resident daemon repair apply preview",
    "value.resident_daemon_launchagent_plan": "resident daemon LaunchAgent plan",
    "value.resident_daemon_service_targets_status": "resident daemon service target status",
    "value.supported_preview_apply_control": "supported: preview, apply, control",
    "value.contract_only": "contract only",
    "value.macos_launchagent": "macOS LaunchAgent",
    "value.linux_systemd_user": "Linux systemd user service",
    "value.windows_service": "Windows Service",
    "value.macos_explicit_cli_only": "macOS explicit CLI only",
    "value.loaded": "loaded",
    "value.not_loaded": "not loaded",
    "value.unsupported_platform": "unsupported platform",
    "value.resident_daemon_launchagent_status": "resident daemon LaunchAgent status",
}

DISPLAY_PHRASE_KEYS: dict[str, str] = {
    "Initialize runtime metadata before daemon start": "phrase.runtime_init_before_start",
    "missing directory may be created with explicit apply intent": "phrase.reason_missing_directory_apply",
    "artifact is present; ownership and liveness are not proven by preview diagnostics": "phrase.reason_artifact_present_review",
    "artifact is present": "phrase.reason_artifact_present_short",
    "artifact is missing; no cleanup is needed": "phrase.reason_artifact_missing_no_cleanup",
    "Inspect missing runtime directories before any control action.": "phrase.reason_inspect_missing_runtime",
    "Review ambiguous daemon artifacts before mutation or control.": "phrase.reason_review_ambiguous_artifacts",
    "Runtime initialization preview currently requires manual review.": "phrase.reason_runtime_init_manual_review",
    "Reviewed stale-file cleanup candidates are available.": "phrase.reason_reviewed_cleanup_available",
    "Missing runtime directories can be reviewed for explicit repair.": "phrase.reason_missing_runtime_repair",
    "Observe bounded readiness signals for the running local daemon.": "phrase.reason_observe_bounded_readiness",
    "Current daemon state is stable; refresh status when needed.": "phrase.reason_state_stable_refresh",
    "Review the current macOS, Linux, and Windows service target contract before service-oriented control.": "phrase.reason_review_service_target_contract",
    "Review the LaunchAgent plist and explicit launchctl commands for the macOS local service line.": "phrase.reason_review_launchagent_preview",
    "A reviewed LaunchAgent plist already exists and may be bootstrapped explicitly.": "phrase.reason_bootstrap_existing_launchagent",
    "Observe whether the reviewed LaunchAgent plist exists and whether launchd currently reports the label as loaded.": "phrase.reason_observe_launchagent_status",
    "The LaunchAgent is already loaded and may be explicitly kickstarted when the service line needs a bounded restart.": "phrase.reason_kickstart_loaded_launchagent",
}

READ_SURFACE_PURPOSE_JA: dict[str, str] = {
    "primary initial screen payload": "初期画面の主要ペイロード",
    "framework-neutral home screen state": "フレームワーク非依存のホーム画面状態",
    "focused daemon diagnostics panel": "重点デーモン診断パネル",
    "framework-neutral daemon panel state": "フレームワーク非依存のデーモンパネル状態",
    "reviewable candidate queue": "レビュー可能な候補キュー",
    "framework-neutral candidate queue state": "フレームワーク非依存の候補キュー状態",
    "candidate detail panel": "候補詳細パネル",
    "framework-neutral candidate detail state": "フレームワーク非依存の候補詳細状態",
    "review diff panel": "レビュー差分パネル",
    "cookie-backed local UI contract read for the Bridge-hosted local shell": "Cookie ベースのローカルUI契約読取（Bridge ホストのローカルシェル向け）",
    "cookie-backed local UI home screen state": "Cookie ベースのローカルUIホーム画面状態",
    "cookie-backed local UI candidate queue state": "Cookie ベースのローカルUI候補キュー状態",
    "cookie-backed local UI candidate detail state": "Cookie ベースのローカルUI候補詳細状態",
    "cookie-backed local UI candidate diff payload": "Cookie ベースのローカルUI候補差分ペイロード",
    "cookie-backed local UI candidate lineage payload": "Cookie ベースのローカルUI候補履歴ペイロード",
    "cookie-backed local UI daemon panel state": "Cookie ベースのローカルUIデーモンパネル状態",
}

BOOTSTRAP_COPY_FEEDBACK: dict[str, str] = {
    "notice.pending_candidate_created": "Pending candidate created from clipboard.",
    "notice.candidate_evaluated": "Candidate evaluated.",
    "notice.candidate_approved": "Candidate approved.",
    "notice.candidate_rejected": "Candidate rejected.",
    "notice.revised_candidate_created": "Revised candidate created.",
    "error.evaluate_before_approve": "Evaluate before approve.",
    "error.candidate_not_evaluated_for_approve": "This candidate is not in evaluated state and cannot be approved.",
    "error.ui_session_required": "Resident app UI session is required. Re-open the local shell.",
    "error.transport_unavailable": "Resident app shell could not reach the Bridge.",
    "error.generic_shell_fetch": "Resident app shell request failed.",
}

BOOTSTRAP_COPY_PHRASES: dict[str, str] = {
    "phrase.runtime_init_before_start": "Initialize runtime metadata before daemon start",
    "phrase.reason_missing_directory_apply": "missing directory may be created with explicit apply intent",
    "phrase.reason_artifact_present_review": "artifact is present; ownership and liveness are not proven by preview diagnostics",
    "phrase.reason_artifact_present_short": "artifact is present",
    "phrase.reason_artifact_missing_no_cleanup": "artifact is missing; no cleanup is needed",
    "phrase.reason_inspect_missing_runtime": "Inspect missing runtime directories before any control action.",
    "phrase.reason_review_ambiguous_artifacts": "Review ambiguous daemon artifacts before mutation or control.",
    "phrase.reason_runtime_init_manual_review": "Runtime initialization preview currently requires manual review.",
    "phrase.reason_reviewed_cleanup_available": "Reviewed stale-file cleanup candidates are available.",
    "phrase.reason_missing_runtime_repair": "Missing runtime directories can be reviewed for explicit repair.",
    "phrase.reason_observe_bounded_readiness": "Observe bounded readiness signals for the running local daemon.",
    "phrase.reason_state_stable_refresh": "Current daemon state is stable; refresh status when needed.",
    "phrase.reason_review_service_target_contract": "Review the current macOS, Linux, and Windows service target contract before service-oriented control.",
    "phrase.reason_review_launchagent_preview": "Review the LaunchAgent plist and explicit launchctl commands for the macOS local service line.",
    "phrase.reason_bootstrap_existing_launchagent": "A reviewed LaunchAgent plist already exists and may be bootstrapped explicitly.",
    "phrase.reason_observe_launchagent_status": "Observe whether the reviewed LaunchAgent plist exists and whether launchd currently reports the label as loaded.",
    "phrase.reason_kickstart_loaded_launchagent": "The LaunchAgent is already loaded and may be explicitly kickstarted when the service line needs a bounded restart.",
}

BOOTSTRAP_COPY: dict[str, str] = (
    BOOTSTRAP_COPY_CORE
    | BOOTSTRAP_COPY_ACTIONS
    | BOOTSTRAP_COPY_LABELS
    | BOOTSTRAP_COPY_DETAILS
    | BOOTSTRAP_COPY_TABLES
    | BOOTSTRAP_COPY_FIELDS
    | BOOTSTRAP_COPY_VALUES
    | BOOTSTRAP_COPY_FEEDBACK
    | BOOTSTRAP_COPY_PHRASES
)

BOOTSTRAP_COPY_JA_CORE: dict[str, str] = {
    "title.home": "紗綾音 Resident App ホーム",
    "title.queue": "紗綾音 Resident App 候補キュー",
    "title.detail": "紗綾音 候補詳細",
    "title.diff": "紗綾音 候補差分",
    "title.daemon": "紗綾音 Resident App デーモンパネル",
    "nav.home": "ホーム",
    "nav.candidates": "候補",
    "nav.daemon": "デーモン",
    "heading.home": "紗綾音 Resident App ホーム",
    "empty.metadata": "表示できるメタデータはありません。",
    "empty.runtime_init_items": "表示できるランタイム初期化項目はありません。",
    "empty.cleanup_decisions": "表示できるクリーンアップ判断はありません。",
    "empty.repair_decisions": "表示できる修復判断はありません。",
    "empty.reviewable_candidates": "レビュー可能な候補はありません。",
    "empty.immediate_daemon_actions": "すぐに必要なデーモン操作はありません。",
    "empty.queue_status_summary": "キュー状態の要約はありません。",
    "empty.section_summary": "セクション要約はありません。",
    "empty.structured_diff_summary": "構造化された差分要約はありません。",
    "heading.queue": "紗綾音 Resident App 候補キュー",
    "heading.detail": "候補詳細",
    "heading.diff": "候補差分",
    "heading.daemon": "紗綾音 Resident App デーモンパネル",
    "desc.home": "Resident App 向けのローカルブリッジ・ブートストラップ画面です。提示専用であり、最終GUIフレームワークではありません。",
    "desc.queue": "アプリ向けキュー上のレビュー可能候補です。提示専用のレビュー画面です。",
    "desc.diff": "差分は承認判断の補助であり、プロファイルを直接変更するものではありません。",
    "desc.daemon": "デーモンパネルはプレビュー指向の観測画面です。プロセス同一性、デーモン準備完了、API準備完了を証明しません。",
    "desc.boundary": "アプリ向け書き込みはプロファイル状態を直接変更しません。デーモンサーフェスもプレビュー指向のままで、プロセス同一性、デーモン準備完了、API準備完了を証明しません。",
    "desc.detail_boundary": "候補レビューは既存のレビュー／承認境界の内側に留まります。",
}

BOOTSTRAP_COPY_JA_ACTIONS: dict[str, str] = {
    "action.open_daemon_panel": "デーモンパネルを開く",
    "action.create_pending_candidate": "保留候補を作成",
    "action.back_to_queue": "キューへ戻る",
    "action.open_diff": "差分を開く",
    "action.back_to_detail": "詳細へ戻る",
    "action.back_to_home": "ホームへ戻る",
    "action.evaluate": "評価する",
    "action.approve": "承認する",
    "action.reject": "却下する",
    "action.create_revised_candidate": "修正版候補を作成",
    "action.refresh": "再読込",
    "action.open_app_shell": "アプリシェルを開く",
    "action.open_legacy_page": "従来ページを開く",
    "action.show_queue": "キューを表示",
    "action.show_daemon": "デーモンを表示",
    "action.show_home": "ホームを表示",
    "action.logout": "UIセッションを終了",
}

BOOTSTRAP_COPY_JA_LABELS: dict[str, str] = {
    "label.repository": "リポジトリ",
    "label.reviewable": "レビュー可能",
    "label.approved_context": "承認済み文脈",
    "label.blocked_context": "保留文脈",
    "label.daemon_state": "デーモン状態",
    "label.next_actions": "次の操作",
    "label.top_review_items": "上位レビュー項目",
    "label.daemon_next_actions": "上位デーモン操作",
    "label.bootstrap_contract": "ブートストラップ契約",
    "label.clipboard_capture": "クリップボード取り込み",
    "label.overview": "概要",
    "label.queue_status_counts": "キュー状態数",
    "label.top_sections": "上位セクション",
    "label.reviewable_count": "レビュー可能数",
    "label.pending": "保留",
    "label.evaluated": "評価済み",
    "label.evaluation_summary": "評価要約",
    "label.operation": "操作",
    "label.content": "内容",
    "label.actions": "操作",
    "label.diff_summary": "差分要約",
    "label.diff_payload": "差分ペイロード",
    "label.runtime_init_preview": "ランタイム初期化プレビュー",
    "label.cleanup_preview": "クリーンアッププレビュー",
    "label.repair_preview": "修復プレビュー",
    "label.service_targets": "サービスターゲット",
    "label.launchagent_preview": "LaunchAgent プレビュー",
    "label.launchagent_status": "LaunchAgent 状態",
    "label.packaging_status": "パッケージング状態",
    "label.service_control_boundary": "サービス制御境界",
    "label.supervision_status": "監視状態",
    "label.recovery_consent_status": "復旧と同意",
    "label.allowed_commands": "許可コマンド",
    "label.deferred_commands": "保留コマンド",
    "label.recommended_flow": "推奨フロー",
    "label.planned_paths": "予定パス",
    "label.cleanup_decisions": "クリーンアップ判断",
    "label.repair_decisions": "修復判断",
    "label.status": "状態",
    "label.section": "セクション",
    "label.source": "ソース",
    "label.running": "稼働中",
    "label.runtime_initialized": "ランタイム初期化済み",
    "label.readiness": "準備状態",
    "label.preferred_entrypoint": "推奨エントリーポイント",
    "label.locale": "表示言語",
    "label.content_field": "内容",
    "label.evaluate_level": "評価レベル",
    "label.override_reason": "上書き理由",
    "label.reject_reason": "却下理由",
    "label.revised_content": "修正後内容",
    "label.target_section": "対象セクション",
    "label.change_reason": "変更理由",
    "label.force_critical_approve": "クリティカル承認を強制する",
    "label.diff_summary_missing": "構造化された差分要約はありません。",
    "label.app_shell": "紗綾音 Resident App シェル",
    "label.lineage": "履歴",
    "label.capture_result": "取り込み結果",
    "label.legacy_surfaces": "従来サーフェス",
    "label.action_forms": "操作フォーム",
    "label.diff_inspection": "差分確認",
    "label.preview_metadata": "プレビュー メタデータ",
    "label.daemon_observation": "デーモン観測",
    "label.quick_links": "クイックリンク",
    "label.queue_summary": "キュー要約",
    "label.reviewable_count_short": "レビュー可能数",
    "label.status_counts_short": "状態数",
    "label.top_sections_short": "上位セクション",
    "label.current_screen": "現在画面",
    "label.current_target": "現在対象",
    "label.json_surface": "JSON サーフェス",
    "label.detail_summary": "詳細要約",
    "label.diff_summary_cards": "差分要約",
    "label.lineage_summary": "履歴要約",
    "label.lineage_events": "履歴イベント",
    "label.proposal_summary": "提案要約",
    "label.evaluation_summary_cards": "評価要約",
    "label.route_state": "ルート状態",
    "label.operator_workspace": "オペレーター作業領域",
    "label.primary_navigation": "主要ナビゲーション",
    "label.session_actions": "セッション操作",
    "label.shell_workspace": "シェル作業領域",
}

BOOTSTRAP_COPY_JA_DETAILS: dict[str, str] = {
    "detail.home_reviewable": "保留または評価済みの候補",
    "detail.home_approved_context": "MCPプレビューに含まれます",
    "detail.home_blocked_context": "MCPプレビューには含まれません",
    "detail.home_next_actions": "優先度の高いデーモン対応",
    "detail.repository_available": "利用可能",
    "detail.repository_unavailable": "利用不可",
    "detail.readiness_prefix": "準備状態",
    "detail.not_evaluated_yet": "未評価です",
    "detail.not_evaluated_short": "未評価",
    "detail.action_guidance": "操作ガイダンス",
    "detail.action_guidance_pending": "承認前に評価を実行してください。承認は既存のレビュー境界により制御されます。",
    "detail.rde_evaluated": "評価済み",
    "detail.rde_class_prefix": "RDE クラス",
    "detail.level_prefix": "レベル",
    "placeholder.clipboard": "ここにクリップボード内容を貼り付けてください",
    "mapping.proposal": "提案",
    "mapping.evaluation": "評価",
    "detail.app_shell_desc": "UIセッションJSONエンドポイントを使うローカル対話シェルです。従来HTMLページはフォールバックとして残ります。",
    "detail.loading": "読み込み中…",
    "detail.empty_lineage": "表示できる履歴イベントはありません。",
    "detail.capture_hint": "クリップボードテキストから保留候補を作成し、このローカルシェル内でレビューを続けます。",
    "detail.detail_unavailable": "候補詳細を表示できません。",
    "detail.fallback_queue_error": "候補詳細の再読込に失敗したため、キューへ戻りました。",
    "detail.enter_reject_reason": "却下理由を入力してください",
    "detail.enter_override_reason": "上書き理由を入力してください（任意）",
    "detail.enter_change_reason": "変更理由を入力してください（任意）",
    "detail.enter_target_section": "対象セクションを入力してください（任意）",
    "detail.enter_revised_content": "候補内容を編集してください",
    "detail.action_unavailable": "この操作は現在の候補状態では利用できません。",
    "detail.empty_next_actions": "すぐに必要なデーモン操作はありません。",
    "detail.empty_preview": "表示できるプレビュー内容はありません。",
    "detail.empty_service_targets": "表示できるサービスターゲットはありません。",
    "detail.empty_launchagent_preview": "このプラットフォームでは LaunchAgent プレビューを利用できません。",
    "detail.empty_launchagent_status": "このプラットフォームでは LaunchAgent 状態を利用できません。",
    "detail.empty_review_items": "表示できるレビュー項目はありません。",
    "detail.empty_quick_links": "表示できるクイックリンクはありません。",
    "detail.target_none": "現在の対象はありません。",
    "detail.empty_diff_summary": "表示できる差分要約はありません。",
    "detail.route_ready": "シェルのルート状態は同期されています。",
    "detail.skip_to_content": "本文へ移動",
    "detail.workspace_desc": "候補キュー、レビュー、取り込み、デーモン観測を要約優先で扱う Resident ワークフローです。",
    "detail.session_action_hint": "logout を使うと Bridge bearer を回さずに、このブラウザセッションだけを無効化できます。",
}

BOOTSTRAP_COPY_JA_TABLES: dict[str, str] = {
    "table.status": "状態",
    "table.section": "セクション",
    "table.evaluation": "評価",
    "table.preview": "プレビュー",
    "table.role": "役割",
    "table.path": "パス",
    "table.reason": "理由",
    "table.recommendation": "推奨",
    "table.target": "対象",
    "table.repairable": "修復可能",
    "table.id": "ID",
    "table.artifact": "アーティファクト",
    "boundary.label": "境界",
}

BOOTSTRAP_COPY_JA_FIELDS: dict[str, str] = {
    "field.id": "ID",
    "field.kind": "種別",
    "field.operation_id": "操作 ID",
    "field.plan_fingerprint": "計画フィンガープリント",
    "field.review_required": "レビュー必須",
    "field.operator_confirmation_signal": "オペレーター確認",
    "field.metadata_path": "メタデータパス",
    "field.preview_hash": "プレビュー ハッシュ",
    "field.allowed_targets": "許可対象",
    "field.decision_policy": "判断ポリシー",
    "field.manual_review_required": "手動レビュー必須",
    "field.section": "セクション",
    "field.operation": "操作",
    "field.level": "レベル",
    "field.status": "状態",
    "field.source": "ソース",
    "field.source_type": "ソース",
    "field.capture_id": "取り込みID",
    "field.decision": "判断",
    "field.rde_class": "RDE クラス",
    "field.events": "イベント数",
    "field.path_role": "役割",
    "field.path": "パス",
    "field.reason": "理由",
    "field.artifact_kind": "アーティファクト",
    "field.diagnostic_status": "状態",
    "field.recommendation": "推奨",
    "field.target": "対象",
    "field.repairable": "修復可能",
    "field.evaluation_level": "評価レベル",
    "field.added_count": "追加数",
    "field.already_present_count": "既存数",
    "field.list_operation": "リスト操作",
}

BOOTSTRAP_COPY_JA_VALUES: dict[str, str] = {
    "value.true": "はい",
    "value.false": "いいえ",
    "value.pending": "保留",
    "value.evaluated": "評価済み",
    "value.approved": "承認済み",
    "value.rejected": "却下済み",
    "value.stopped": "停止中",
    "value.readiness_not_ready": "未準備",
    "value.review_required": "レビュー要",
    "value.manual_review_required": "手動レビュー要",
    "value.present_review_required": "要レビューで存在",
    "value.action": "操作",
    "value.create": "作成",
    "value.missing": "未作成",
    "value.runtime_init": "ランタイム初期化",
    "value.runtime_root": "ランタイムルート",
    "value.pid_dir": "PID ディレクトリ",
    "value.lock_dir": "ロックディレクトリ",
    "value.socket_dir": "ソケットディレクトリ",
    "value.log_dir": "ログディレクトリ",
    "value.temp_dir": "一時ディレクトリ",
    "value.state_dir": "状態ディレクトリ",
    "value.pid_file": "PID ファイル",
    "value.lock_file": "ロックファイル",
    "value.socket_file": "ソケットファイル",
    "value.available": "利用可能",
    "value.unavailable": "利用不可",
    "value.clipboard": "クリップボード",
    "value.selection": "選択範囲",
    "value.page": "ページ",
    "value.manual": "手動",
    "value.knowledge.concepts": "知識 / 概念",
    "value.important_terms": "重要語",
    "value.add": "追加",
    "value.list_add": "リスト追加",
    "value.no_action": "操作不要",
    "value.resident_daemon_runtime_init_plan": "Resident Daemon ランタイム初期化計画",
    "value.resident_daemon_cleanup_apply_preview": "Resident Daemon クリーンアップ適用プレビュー",
    "value.resident_daemon_repair_apply_preview": "Resident Daemon 修復適用プレビュー",
    "value.resident_daemon_launchagent_plan": "Resident Daemon LaunchAgent 計画",
    "value.resident_daemon_service_targets_status": "Resident Daemon サービスターゲット状態",
    "value.supported_preview_apply_control": "対応済み（preview / apply / control）",
    "value.contract_only": "契約のみ",
    "value.macos_launchagent": "macOS LaunchAgent",
    "value.linux_systemd_user": "Linux systemd ユーザーサービス",
    "value.windows_service": "Windows サービス",
    "value.macos_explicit_cli_only": "macOS 明示CLI専用",
    "value.loaded": "読込済み",
    "value.not_loaded": "未読込",
    "value.unsupported_platform": "対象外プラットフォーム",
    "value.resident_daemon_launchagent_status": "Resident Daemon LaunchAgent 状態",
}

BOOTSTRAP_COPY_JA_FEEDBACK: dict[str, str] = {
    "notice.pending_candidate_created": "クリップボードから保留候補を作成しました。",
    "notice.candidate_evaluated": "候補を評価しました。",
    "notice.candidate_approved": "候補を承認しました。",
    "notice.candidate_rejected": "候補を却下しました。",
    "notice.revised_candidate_created": "修正版候補を作成しました。",
    "error.evaluate_before_approve": "承認前に評価してください。",
    "error.candidate_not_evaluated_for_approve": "この候補は評価済み状態ではないため承認できません。",
    "error.ui_session_required": "Resident App UI セッションが必要です。ローカルシェルを開き直してください。",
    "error.transport_unavailable": "Resident AppシェルからBridgeに接続できませんでした。",
    "error.generic_shell_fetch": "Resident Appシェルのリクエストに失敗しました。",
}

BOOTSTRAP_COPY_JA_PHRASES: dict[str, str] = {
    "phrase.runtime_init_before_start": "デーモン起動前にランタイムメタデータを初期化します",
    "phrase.reason_missing_directory_apply": "不足ディレクトリは明示的な適用意図のもとで作成できます",
    "phrase.reason_artifact_present_review": "アーティファクトは存在しますが、所有権と稼働状態はプレビュー診断だけでは証明されません",
    "phrase.reason_artifact_present_short": "アーティファクトは存在します",
    "phrase.reason_artifact_missing_no_cleanup": "アーティファクトが存在しないため、クリーンアップは不要です。",
    "phrase.reason_inspect_missing_runtime": "制御操作前に不足しているランタイムディレクトリを確認します。",
    "phrase.reason_review_ambiguous_artifacts": "変更や制御の前に曖昧なデーモンアーティファクトを確認します。",
    "phrase.reason_runtime_init_manual_review": "ランタイム初期化プレビューは現在手動レビューを要します。",
    "phrase.reason_reviewed_cleanup_available": "レビュー済みの古いファイル向けクリーンアップ候補を利用できます。",
    "phrase.reason_missing_runtime_repair": "不足しているランタイムディレクトリは明示的な修復対象として確認できます。",
    "phrase.reason_observe_bounded_readiness": "実行中のローカルデーモンについて境界付きの準備状態シグナルを観測します。",
    "phrase.reason_state_stable_refresh": "現在のデーモン状態は安定しています。必要に応じて状態を更新してください。",
    "phrase.reason_review_service_target_contract": "サービス指向の制御前に、macOS・Linux・Windows のサービスターゲット契約を確認します。",
    "phrase.reason_review_launchagent_preview": "macOS ローカルサービス系統向けに LaunchAgent plist と明示的な launchctl コマンドを確認します。",
    "phrase.reason_bootstrap_existing_launchagent": "レビュー済みの LaunchAgent plist がすでに存在するため、明示的に bootstrap できます。",
    "phrase.reason_observe_launchagent_status": "レビュー済み LaunchAgent plist の存在有無と、launchd が現在そのラベルを読込済みとして報告するかを観測します。",
    "phrase.reason_kickstart_loaded_launchagent": "LaunchAgent がすでに読込済みのため、サービス系統に境界付き再起動が必要な場合は明示的に kickstart できます。",
}

BOOTSTRAP_COPY_JA: dict[str, str] = (
    BOOTSTRAP_COPY_JA_CORE
    | BOOTSTRAP_COPY_JA_ACTIONS
    | BOOTSTRAP_COPY_JA_LABELS
    | BOOTSTRAP_COPY_JA_DETAILS
    | BOOTSTRAP_COPY_JA_TABLES
    | BOOTSTRAP_COPY_JA_FIELDS
    | BOOTSTRAP_COPY_JA_VALUES
    | BOOTSTRAP_COPY_JA_FEEDBACK
    | BOOTSTRAP_COPY_JA_PHRASES
)


def normalize_bootstrap_locale(locale: str | None) -> str:
    if not locale:
        return DEFAULT_BOOTSTRAP_LOCALE
    base = locale.strip().replace("_", "-").split("-")[0].lower()
    return "ja" if base == "ja" else "en"


def _copy(key: str, locale: str = DEFAULT_BOOTSTRAP_LOCALE) -> str:
    if locale == "ja":
        return BOOTSTRAP_COPY_JA.get(key, BOOTSTRAP_COPY[key])
    return BOOTSTRAP_COPY[key]


def bootstrap_copy(key: str, locale: str = DEFAULT_BOOTSTRAP_LOCALE) -> str:
    return _copy(key, locale)


def translate_bootstrap_feedback(message: str | None, locale: str = DEFAULT_BOOTSTRAP_LOCALE) -> str | None:
    if not message:
        return message
    feedback_keys = {
        "Pending candidate created from clipboard.": "notice.pending_candidate_created",
        "Candidate evaluated.": "notice.candidate_evaluated",
        "Candidate approved.": "notice.candidate_approved",
        "Candidate rejected.": "notice.candidate_rejected",
        "Revised candidate created.": "notice.revised_candidate_created",
        "Evaluate before approve.": "error.evaluate_before_approve",
        "This candidate is not in evaluated state and cannot be approved.": "error.candidate_not_evaluated_for_approve",
        "Missing or invalid resident app UI session": "error.ui_session_required",
    }
    copy_key = feedback_keys.get(message)
    if copy_key is None and message.startswith(
        "This candidate is not in evaluated state and cannot be approved."
    ):
        copy_key = "error.candidate_not_evaluated_for_approve"
    return _copy(copy_key, locale) if copy_key else message


def _translate_display_phrase(text: str | None, locale: str = DEFAULT_BOOTSTRAP_LOCALE) -> str:
    if not text:
        return ""
    copy_key = DISPLAY_PHRASE_KEYS.get(text)
    return _copy(copy_key, locale) if copy_key else text


def _translate_display_token(value: Any, locale: str = DEFAULT_BOOTSTRAP_LOCALE) -> str:
    if value is True:
        return _copy("value.true", locale)
    if value is False:
        return _copy("value.false", locale)
    if value is None:
        return "—"
    if isinstance(value, (list, tuple)):
        return ", ".join(_translate_display_token(item, locale) for item in value) or "—"
    string_value = str(value)
    lookup_key = f"value.{string_value}"
    copy_source = BOOTSTRAP_COPY_JA if locale == "ja" else BOOTSTRAP_COPY
    if lookup_key in copy_source or lookup_key in BOOTSTRAP_COPY:
        return _copy(lookup_key, locale)
    localized_rde_class = rde_class_label(string_value, locale)
    if localized_rde_class != string_value:
        return localized_rde_class
    return string_value


def _translate_display_key(key: str, locale: str = DEFAULT_BOOTSTRAP_LOCALE) -> str:
    copy_key = f"field.{key}"
    copy_source = BOOTSTRAP_COPY_JA if locale == "ja" else BOOTSTRAP_COPY
    if copy_key in copy_source or copy_key in BOOTSTRAP_COPY:
        return _copy(copy_key, locale)
    return key.replace("_", " ")


def _translate_read_surface_purpose(text: str | None, locale: str = DEFAULT_BOOTSTRAP_LOCALE) -> str:
    if not text:
        return ""
    if locale == "ja":
        return READ_SURFACE_PURPOSE_JA.get(text, text)
    return text


def _page(
    title: str,
    body: str,
    *,
    locale: str = DEFAULT_BOOTSTRAP_LOCALE,
    notice: str | None = None,
    error: str | None = None,
) -> str:
    flash = ""
    if notice:
        flash += f'<div class="flash flash-notice">{escape(notice)}</div>'
    if error:
        flash += f'<div class="flash flash-error">{escape(error)}</div>'
    return f"""<!DOCTYPE html>
<html lang="{escape(locale)}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
.skip-link {{ position:absolute; left:16px; top:-48px; background:#0f172a; color:#fff; padding:10px 14px; border-radius:8px; z-index:100; text-decoration:none; }}
.skip-link:focus {{ top:16px; }}
.shell {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
.app-header {{ display:grid; gap:12px; margin-bottom:20px; }}
.app-header-copy {{ display:grid; gap:6px; }}
.nav {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; align-items:center; }}
.nav a {{ color: #2563eb; text-decoration: none; font-weight: 600; padding: 8px 10px; border-radius: 8px; }}
.nav a[aria-current="page"] {{ background:#dbeafe; color:#1d4ed8; }}
h1 {{ font-size: 1.8rem; margin-bottom: 4px; }}
h2 {{ font-size: 1.1rem; margin: 28px 0 12px; }}
h3 {{ margin: 0 0 12px 0; }}
p {{ line-height: 1.5; }}
.muted {{ color: #64748b; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
.card {{ background: white; border-radius: 10px; padding: 16px; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08); }}
.label {{ font-size: .75rem; text-transform: uppercase; color: #64748b; }}
.value {{ font-size: 1.5rem; font-weight: 700; margin-top: 6px; }}
.detail {{ font-size: .8rem; color: #64748b; margin-top: 6px; }}
.panel {{ background: white; border-radius: 12px; padding: 16px; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08); margin-bottom: 16px; border:1px solid #e2e8f0; }}
ul {{ margin: 0; padding-left: 20px; }}
li {{ margin: 10px 0; }}
code {{ background: #e2e8f0; border-radius: 4px; padding: 2px 6px; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #f8fafc; padding: 12px; border-radius: 8px; }}
table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }}
th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
th {{ background: #e2e8f0; }}
.kv {{ display:grid; grid-template-columns: minmax(160px, 220px) minmax(0, 1fr); gap: 8px 12px; margin:0; }}
.kv dt {{ font-weight: 600; color:#334155; }}
.kv dd {{ margin:0; color:#0f172a; word-break: break-word; }}
.compact-table th, .compact-table td {{ padding: 8px 10px; font-size: .92rem; }}
.boundary {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 14px; border-radius: 6px; margin-top: 24px; }}
.flash {{ border-radius: 8px; padding: 12px 14px; margin: 0 0 16px 0; }}
.flash-notice {{ background: #dcfce7; color: #166534; border-left: 4px solid #22c55e; }}
.flash-error {{ background: #fee2e2; color: #991b1b; border-left: 4px solid #ef4444; }}
.pill {{ display:inline-block; border-radius:999px; padding:2px 8px; font-size:.75rem; font-weight:600; background:#e2e8f0; color:#334155; margin-right:6px; }}
.pill-pending {{ background:#fef3c7; color:#92400e; }}
.pill-evaluated {{ background:#dbeafe; color:#1d4ed8; }}
.pill-approved {{ background:#dcfce7; color:#166534; }}
.pill-rejected {{ background:#fee2e2; color:#991b1b; }}
.pill-warning {{ background:#fef3c7; color:#92400e; }}
textarea, input {{ font: inherit; }}
button {{ font: inherit; cursor: pointer; border: 1px solid #cbd5e1; background: white; border-radius: 8px; padding: 8px 12px; }}
button:hover {{ background: #f8fafc; }}
a, button, input, textarea {{ transition: box-shadow .12s ease, border-color .12s ease, background .12s ease; }}
a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible {{ outline:none; box-shadow:0 0 0 3px rgba(37,99,235,.25); border-color:#2563eb; }}
.link-button {{ border: 0; background: transparent; color: #2563eb; padding: 0; font-weight: 600; }}
.resident-shell-toolbar {{ display:flex; gap:10px; flex-wrap:wrap; margin: 0 0 16px 0; }}
.resident-app-shell-root {{ display:grid; gap:16px; }}
.shell-form-grid {{ display:grid; gap:12px; }}
.shell-form-grid textarea, .shell-form-grid input {{ width:100%; box-sizing:border-box; }}
button:disabled {{ cursor:not-allowed; opacity:.55; }}
.shell-action-grid {{ display:grid; gap:16px; }}
.shell-nav-active {{ background:#dbeafe; border-color:#93c5fd; color:#1d4ed8; }}
.shell-grid {{ display:grid; gap:16px; }}
.shell-meta {{ display:grid; gap:12px; grid-template-columns: minmax(0, 1fr) auto; align-items:start; }}
.shell-session-panel {{ display:grid; gap:10px; justify-items:start; }}
.shell-table-wrap {{ overflow-x:auto; }}
@media (min-width: 960px) {{
  .shell-grid.two-up {{ grid-template-columns: minmax(0, 1.15fr) minmax(320px, .85fr); }}
}}
@media (max-width: 720px) {{
  .shell {{ padding: 16px; }}
  .kv {{ grid-template-columns: 1fr; }}
  .nav {{ gap: 8px; }}
  .cards {{ grid-template-columns: 1fr; }}
  th, td {{ padding: 10px; }}
  .shell-meta {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<a class="skip-link" href="#main-content">{escape(_copy("detail.skip_to_content", locale))}</a>
<main id="main-content" class="shell" tabindex="-1">
<header class="app-header">
<div class="app-header-copy">
<h1>{escape(title)}</h1>
</div>
<nav class="nav" aria-label="{escape(_copy('label.primary_navigation', locale))}">
<a href="/app/ui">{escape(_copy("nav.home", locale))}</a>
<a href="/app/ui/candidates">{escape(_copy("nav.candidates", locale))}</a>
<a href="/app/ui/daemon">{escape(_copy("nav.daemon", locale))}</a>
</nav>
</header>
{flash}
{body}
</main>
</body>
</html>
"""


def _render_kv_panel(locale: str, data: dict[str, Any], *, keys: list[str] | None = None) -> str:
    selected_keys = keys or list(data.keys())
    rows = "".join(
        f"<dt>{escape(_translate_display_key(key, locale))}</dt><dd>{escape(_translate_display_token(data.get(key), locale))}</dd>"
        for key in selected_keys
        if key in data
    )
    return f"<dl class=\"kv\">{rows}</dl>" if rows else f'<p class="muted">{escape(_copy("empty.metadata", locale))}</p>'


def _render_json_fallback(payload: Any) -> str:
    return f"<pre>{escape(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))}</pre>"


def _render_card(
    label: str,
    value: Any,
    detail: str = "",
    *,
    value_font_size: str | None = None,
    detail_is_html: bool = False,
) -> str:
    if detail:
        detail_body = detail if detail_is_html else escape(detail)
        detail_html = f'<div class="detail">{detail_body}</div>'
    else:
        detail_html = ""
    value_style = f' style="font-size:{escape(value_font_size)};"' if value_font_size else ""
    return (
        '<section class="card">'
        f'<div class="label">{escape(label)}</div>'
        f'<div class="value"{value_style}>{escape(str(value))}</div>'
        f"{detail_html}"
        "</section>"
    )


def _render_cards_grid(cards: list[str]) -> str:
    return f'<div class="cards">{"".join(cards)}</div>'


def _render_panel(title: str, content: str) -> str:
    return f'<div class="panel"><h2>{escape(title)}</h2>{content}</div>'


def _render_panel_without_title(content: str) -> str:
    return f'<div class="panel">{content}</div>'


def _render_string_list(items: list[str], *, empty_label: str) -> str:
    if not items:
        return f'<p class="muted">{escape(empty_label)}</p>'
    rows = "".join(f"<li><code>{escape(item)}</code></li>" for item in items)
    return f"<ul>{rows}</ul>"


def _render_runtime_init_preview(locale: str, payload: dict[str, Any]) -> str:
    items = payload.get("items", [])
    item_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(_translate_display_token(item.get('path_role', ''), locale))}</td>"
            f"<td>{escape(_translate_display_token(item.get('status', ''), locale))}</td>"
            f"<td>{escape(str(item.get('path', '')))}</td>"
            f"<td>{escape(_translate_display_phrase(str(item.get('reason', '')), locale))}</td>"
            "</tr>"
        )
        for item in items
    ) or f'<tr><td colspan="4" class="muted">{escape(_copy("empty.runtime_init_items", locale))}</td></tr>'
    return (
        f"{_render_kv_panel(locale, payload, keys=['kind', 'operation_id', 'plan_fingerprint', 'review_required', 'operator_confirmation_signal', 'metadata_path'])}"
        f"<h3>{escape(_copy('label.planned_paths', locale))}</h3>"
        f'<table class="compact-table"><thead><tr><th>{escape(_copy("table.role", locale))}</th><th>{escape(_copy("table.status", locale))}</th><th>{escape(_copy("table.path", locale))}</th><th>{escape(_copy("table.reason", locale))}</th></tr></thead>'
        f"<tbody>{item_rows}</tbody></table>"
    )


def _render_cleanup_preview(locale: str, payload: dict[str, Any]) -> str:
    decision_report = payload.get("decision_report", {})
    decisions = decision_report.get("decisions", [])
    decision_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(_translate_display_token(item.get('artifact_kind', ''), locale))}</td>"
            f"<td>{escape(_translate_display_token(item.get('diagnostic_status', ''), locale))}</td>"
            f"<td>{escape(_translate_display_token(item.get('recommendation', ''), locale))}</td>"
            f"<td>{escape(_translate_display_phrase(str(item.get('reason', '')), locale))}</td>"
            "</tr>"
        )
        for item in decisions
    ) or f'<tr><td colspan="4" class="muted">{escape(_copy("empty.cleanup_decisions", locale))}</td></tr>'
    metadata = {
        "kind": payload.get("kind"),
        "operation_id": payload.get("operation_id"),
        "preview_hash": payload.get("preview_hash"),
        "allowed_targets": payload.get("allowed_targets", []),
        "decision_policy": decision_report.get("decision_policy"),
        "manual_review_required": decision_report.get("manual_review_required"),
    }
    return (
        f"{_render_kv_panel(locale, metadata)}"
        f"<h3>{escape(_copy('label.cleanup_decisions', locale))}</h3>"
        f'<table class="compact-table"><thead><tr><th>{escape(_copy("table.artifact", locale))}</th><th>{escape(_copy("table.status", locale))}</th><th>{escape(_copy("table.recommendation", locale))}</th><th>{escape(_copy("table.reason", locale))}</th></tr></thead>'
        f"<tbody>{decision_rows}</tbody></table>"
    )


def _render_repair_preview(locale: str, payload: dict[str, Any]) -> str:
    decisions = payload.get("decisions", {})
    decision_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(_translate_display_token(target, locale))}</td>"
            f"<td>{escape(_translate_display_token(item.get('status', ''), locale))}</td>"
            f"<td>{escape(_translate_display_token(item.get('repairable', ''), locale))}</td>"
            f"<td>{escape(str(item.get('path', '')))}</td>"
            "</tr>"
        )
        for target, item in decisions.items()
    ) or f'<tr><td colspan="4" class="muted">{escape(_copy("empty.repair_decisions", locale))}</td></tr>'
    metadata = {
        "kind": payload.get("kind"),
        "operation_id": payload.get("operation_id"),
        "preview_hash": payload.get("preview_hash"),
        "allowed_targets": payload.get("allowed_targets", []),
    }
    return (
        f"{_render_kv_panel(locale, metadata)}"
        f"<h3>{escape(_copy('label.repair_decisions', locale))}</h3>"
        f'<table class="compact-table"><thead><tr><th>{escape(_copy("table.target", locale))}</th><th>{escape(_copy("table.status", locale))}</th><th>{escape(_copy("table.repairable", locale))}</th><th>{escape(_copy("table.path", locale))}</th></tr></thead>'
        f"<tbody>{decision_rows}</tbody></table>"
    )


def _render_service_targets_status(locale: str, payload: dict[str, Any]) -> str:
    targets = payload.get("targets", [])
    target_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(_translate_display_token(item.get('target', ''), locale))}</td>"
            f"<td>{escape(_translate_display_token(item.get('platform', ''), locale))}</td>"
            f"<td>{escape(str(item.get('service_manager', '')))}</td>"
            f"<td>{escape(_translate_display_token(item.get('status', ''), locale))}</td>"
            "</tr>"
        )
        for item in targets
    ) or f'<tr><td colspan="4" class="muted">{escape(_copy("detail.empty_service_targets", locale))}</td></tr>'
    metadata = {
        "kind": payload.get("kind"),
        "current_platform": payload.get("current_platform"),
        "recommended_target": payload.get("recommended_target"),
    }
    return (
        f"{_render_kv_panel(locale, metadata)}"
        '<table class="compact-table"><thead><tr>'
        f'<th>{escape(_copy("table.target", locale))}</th>'
        f'<th>{escape(_copy("field.section", locale).replace("Section", "Platform").replace("セクション", "プラットフォーム"))}</th>'
        f'<th>{escape(_copy("label.operation", locale).replace("Operation", "Service Manager").replace("操作", "サービスマネージャ"))}</th>'
        f'<th>{escape(_copy("table.status", locale))}</th>'
        '</tr></thead>'
        f"<tbody>{target_rows}</tbody></table>"
    )


def _render_launchagent_preview(locale: str, payload: dict[str, Any] | None) -> str:
    if not payload:
        return f'<p class="muted">{escape(_copy("detail.empty_launchagent_preview", locale))}</p>'
    metadata = {
        "kind": payload.get("kind"),
        "operation_id": payload.get("operation_id"),
        "preview_hash": payload.get("preview_hash"),
        "label": payload.get("label"),
        "plist_path": payload.get("plist_path"),
    }
    command_items = "".join(
        f"<li><strong>{escape(name)}</strong>: <code>{escape(command)}</code></li>"
        for name, command in payload.get("launchctl_commands", {}).items()
    ) or f'<li class="muted">{escape(_copy("detail.empty_preview", locale))}</li>'
    return f"{_render_kv_panel(locale, metadata)}<ul>{command_items}</ul>"


def _render_launchagent_status(locale: str, payload: dict[str, Any] | None) -> str:
    if not payload:
        return f'<p class="muted">{escape(_copy("detail.empty_launchagent_status", locale))}</p>'
    return _render_kv_panel(
        locale,
        payload,
        keys=[
            "kind",
            "label",
            "plist_path",
            "plist_exists",
            "loaded_status",
            "service_manager",
        ],
    )


def _render_candidate_mapping(locale: str, title: str, payload: dict[str, Any]) -> str:
    return _render_panel(title, f"{_render_kv_panel(locale, payload)}{_render_json_fallback(payload)}")


def _render_resident_app_shell_bootstrap(
    contract: dict[str, Any],
    overview: dict[str, Any],
    *,
    locale: str,
) -> str:
    from sayane.app import build_home_screen_state

    bootstrap = {
        "locale": locale,
        "strings": {
            "appShell": _copy("label.app_shell", locale),
            "appShellDesc": _copy("detail.app_shell_desc", locale),
            "loading": _copy("detail.loading", locale),
            "overview": _copy("label.overview", locale),
            "queue": _copy("nav.candidates", locale),
            "daemon": _copy("nav.daemon", locale),
            "content": _copy("label.content_field", locale),
            "lineage": _copy("label.lineage", locale),
            "actions": _copy("label.actions", locale),
            "actionForms": _copy("label.action_forms", locale),
            "diffInspection": _copy("label.diff_inspection", locale),
            "previewMetadata": _copy("label.preview_metadata", locale),
            "daemonObservation": _copy("label.daemon_observation", locale),
            "quickLinks": _copy("label.quick_links", locale),
            "queueSummary": _copy("label.queue_summary", locale),
            "currentScreen": _copy("label.current_screen", locale),
            "currentTarget": _copy("label.current_target", locale),
            "jsonSurface": _copy("label.json_surface", locale),
            "detailSummary": _copy("label.detail_summary", locale),
            "diffSummaryCards": _copy("label.diff_summary_cards", locale),
            "lineageSummary": _copy("label.lineage_summary", locale),
            "lineageEvents": _copy("label.lineage_events", locale),
            "proposalSummary": _copy("label.proposal_summary", locale),
            "evaluationSummaryCards": _copy("label.evaluation_summary_cards", locale),
            "routeState": _copy("label.route_state", locale),
            "operatorWorkspace": _copy("label.operator_workspace", locale),
            "sessionActions": _copy("label.session_actions", locale),
            "shellWorkspace": _copy("label.shell_workspace", locale),
            "captureResult": _copy("label.capture_result", locale),
            "legacySurfaces": _copy("label.legacy_surfaces", locale),
            "refresh": _copy("action.refresh", locale),
            "showHome": _copy("action.show_home", locale),
            "showQueue": _copy("action.show_queue", locale),
            "showDaemon": _copy("action.show_daemon", locale),
            "logout": _copy("action.logout", locale),
            "openLegacyPage": _copy("action.open_legacy_page", locale),
            "createPendingCandidate": _copy("action.create_pending_candidate", locale),
            "createRevisedCandidate": _copy("action.create_revised_candidate", locale),
            "evaluate": _copy("action.evaluate", locale),
            "approve": _copy("action.approve", locale),
            "reject": _copy("action.reject", locale),
            "openDiff": _copy("action.open_diff", locale),
            "backToQueue": _copy("action.back_to_queue", locale),
            "clipboardPlaceholder": _copy("placeholder.clipboard", locale),
            "captureHint": _copy("detail.capture_hint", locale),
            "emptyLineage": _copy("detail.empty_lineage", locale),
            "detailUnavailable": _copy("detail.detail_unavailable", locale),
            "fallbackQueueError": _copy("detail.fallback_queue_error", locale),
            "authFailure": _copy("error.ui_session_required", locale),
            "transportFailure": _copy("error.transport_unavailable", locale),
            "genericShellFetch": _copy("error.generic_shell_fetch", locale),
            "noticePendingCandidateCreated": _copy("notice.pending_candidate_created", locale),
            "noticeCandidateEvaluated": _copy("notice.candidate_evaluated", locale),
            "noticeCandidateApproved": _copy("notice.candidate_approved", locale),
            "noticeCandidateRejected": _copy("notice.candidate_rejected", locale),
            "noticeRevisedCandidateCreated": _copy("notice.revised_candidate_created", locale),
            "enterRejectReason": _copy("detail.enter_reject_reason", locale),
            "enterOverrideReason": _copy("detail.enter_override_reason", locale),
            "enterChangeReason": _copy("detail.enter_change_reason", locale),
            "enterTargetSection": _copy("detail.enter_target_section", locale),
            "enterRevisedContent": _copy("detail.enter_revised_content", locale),
            "actionUnavailable": _copy("detail.action_unavailable", locale),
            "emptyNextActions": _copy("detail.empty_next_actions", locale),
            "emptyPreview": _copy("detail.empty_preview", locale),
            "emptyReviewableCandidates": _copy("empty.reviewable_candidates", locale),
            "emptyReviewItems": _copy("detail.empty_review_items", locale),
            "emptyQuickLinks": _copy("detail.empty_quick_links", locale),
            "targetNone": _copy("detail.target_none", locale),
            "emptyDiffSummary": _copy("detail.empty_diff_summary", locale),
            "routeReady": _copy("detail.route_ready", locale),
            "workspaceDesc": _copy("detail.workspace_desc", locale),
            "sessionActionHint": _copy("detail.session_action_hint", locale),
            "evaluateLevel": _copy("label.evaluate_level", locale),
            "overrideReason": _copy("label.override_reason", locale),
            "rejectReason": _copy("label.reject_reason", locale),
            "revisedContent": _copy("label.revised_content", locale),
            "targetSection": _copy("label.target_section", locale),
            "changeReason": _copy("label.change_reason", locale),
            "forceCriticalApprove": _copy("label.force_critical_approve", locale),
            "daemonState": _copy("label.daemon_state", locale),
            "running": _copy("label.running", locale),
            "runtimeInitialized": _copy("label.runtime_initialized", locale),
            "readiness": _copy("label.readiness", locale),
            "nextActions": _copy("label.next_actions", locale),
            "runtimeInitPreview": _copy("label.runtime_init_preview", locale),
            "cleanupPreview": _copy("label.cleanup_preview", locale),
            "repairPreview": _copy("label.repair_preview", locale),
            "packagingStatus": _copy("label.packaging_status", locale),
            "serviceControlBoundary": _copy("label.service_control_boundary", locale),
            "supervisionStatus": _copy("label.supervision_status", locale),
            "recoveryConsentStatus": _copy("label.recovery_consent_status", locale),
            "serviceTargets": _copy("label.service_targets", locale),
            "launchagentPreview": _copy("label.launchagent_preview", locale),
            "launchagentStatus": _copy("label.launchagent_status", locale),
            "allowedCommands": _copy("label.allowed_commands", locale),
            "deferredCommands": _copy("label.deferred_commands", locale),
            "recommendedFlow": _copy("label.recommended_flow", locale),
            "reviewableCountShort": _copy("label.reviewable_count_short", locale),
            "statusCountsShort": _copy("label.status_counts_short", locale),
            "topSectionsShort": _copy("label.top_sections_short", locale),
            "repository": _copy("label.repository", locale),
            "reviewable": _copy("label.reviewable", locale),
            "approvedContext": _copy("label.approved_context", locale),
            "blockedContext": _copy("label.blocked_context", locale),
            "screenHome": _copy("nav.home", locale),
            "screenQueue": _copy("nav.candidates", locale),
            "screenDetail": _copy("heading.detail", locale),
            "screenDaemon": _copy("nav.daemon", locale),
        },
        "tableLabels": {
            key.removeprefix("table."): _copy(key, locale)
            for key in BOOTSTRAP_COPY_TABLES
            if key.startswith("table.")
        },
        "fieldLabels": {
            key.removeprefix("field."): _copy(key, locale)
            for key in BOOTSTRAP_COPY_FIELDS
            if key.startswith("field.")
        },
        "valueLabels": {
            key.removeprefix("value."): _copy(key, locale)
            for key in BOOTSTRAP_COPY_VALUES
            if key.startswith("value.")
        },
        "phraseLabels": {
            text: _copy(copy_key, locale)
            for text, copy_key in DISPLAY_PHRASE_KEYS.items()
        },
        "contract": contract,
        "overview": overview,
        "homeState": build_home_screen_state(overview),
        "endpoints": {
            "contract": "/app/ui-state/contract",
            "home": "/app/ui-state/home",
            "queue": "/app/ui-state/candidates",
            "detail": "/app/ui-state/candidates/{id}",
            "diff": "/app/ui-state/candidates/{id}/diff",
            "lineage": "/app/ui-state/candidates/{id}/lineage",
            "daemon": "/app/ui-state/daemon",
            "capture": "/app/ui-action/capture-clipboard",
            "evaluate": "/app/ui-action/candidates/{id}/evaluate",
            "approve": "/app/ui-action/candidates/{id}/approve",
            "reject": "/app/ui-action/candidates/{id}/reject",
            "revise": "/app/ui-action/candidates/{id}/revise",
            "logout": "/app/ui-action/session/logout",
        },
        "legacyPaths": {
            "home": "/app/ui",
            "queue": "/app/ui/candidates",
            "daemon": "/app/ui/daemon",
            "detail": "/app/ui/candidates/{id}",
            "diff": "/app/ui/candidates/{id}/diff",
        },
    }
    payload = json.dumps(bootstrap, ensure_ascii=False).replace("</", "<\\/")
    return f"""
<section id="resident-app-shell-section">
<h2>{escape(_copy("label.app_shell", locale))}</h2>
<p class="muted">{escape(_copy("detail.app_shell_desc", locale))}</p>
<div class="panel shell-meta">
  <div>
    <div class="label">{escape(_copy("label.operator_workspace", locale))}</div>
    <p class="muted">{escape(_copy("detail.workspace_desc", locale))}</p>
  </div>
  <div class="shell-session-panel">
    <div class="label">{escape(_copy("label.session_actions", locale))}</div>
    <button type="button" data-shell-logout>{escape(_copy("action.logout", locale))}</button>
    <div class="detail">{escape(_copy("detail.session_action_hint", locale))}</div>
  </div>
</div>
<div class="resident-shell-toolbar" aria-label="{escape(_copy('label.primary_navigation', locale))}">
  <button type="button" data-shell-nav="home">{escape(_copy("action.show_home", locale))}</button>
  <button type="button" data-shell-nav="queue">{escape(_copy("action.show_queue", locale))}</button>
  <button type="button" data-shell-nav="daemon">{escape(_copy("action.show_daemon", locale))}</button>
  <button type="button" data-shell-refresh>{escape(_copy("action.refresh", locale))}</button>
</div>
<div id="resident-app-shell-status" class="flash" role="status" aria-live="polite" tabindex="-1" hidden></div>
<div id="resident-app-shell-root" class="resident-app-shell-root" aria-label="{escape(_copy('label.shell_workspace', locale))}">
  <div class="panel"><p class="muted">{escape(_copy("detail.loading", locale))}</p></div>
</div>
<script id="resident-app-bootstrap-data" type="application/json">{payload}</script>
<script>
(() => {{
  const dataNode = document.getElementById("resident-app-bootstrap-data");
  const root = document.getElementById("resident-app-shell-root");
  const statusNode = document.getElementById("resident-app-shell-status");
  if (!dataNode || !root || !statusNode) return;
  const bootstrap = JSON.parse(dataNode.textContent || "{{}}");
  const strings = bootstrap.strings || {{}};
  const tableLabels = bootstrap.tableLabels || {{}};
  const fieldLabels = bootstrap.fieldLabels || {{}};
  const valueLabels = bootstrap.valueLabels || {{}};
  const phraseLabels = bootstrap.phraseLabels || {{}};
  const endpoints = bootstrap.endpoints || {{}};
  const legacyPaths = bootstrap.legacyPaths || {{}};
  const state = {{
    screen: "home",
    candidateId: null,
    contract: bootstrap.contract || null,
    overview: bootstrap.overview || null,
    homeState: bootstrap.homeState || null,
    queueState: null,
    detailState: null,
    detailDiff: null,
    detailLineage: null,
    daemonState: null,
    lastCapture: null,
  }};

  function parseRouteHash() {{
    const raw = window.location.hash.startsWith("#") ? window.location.hash.slice(1) : window.location.hash;
    const params = new URLSearchParams(raw);
    return {{
      screen: params.get("screen") || "home",
      candidateId: params.get("candidate_id"),
    }};
  }}

  function syncRouteHash() {{
    const params = new URLSearchParams();
    params.set("screen", state.screen);
    if (state.candidateId) params.set("candidate_id", state.candidateId);
    const nextHash = `#${{params.toString()}}`;
    if (window.location.hash !== nextHash) {{
      window.history.replaceState(null, "", nextHash);
    }}
  }}

  function text(value) {{
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "boolean") return value ? "true" : "false";
    if (Array.isArray(value)) return value.map((item) => text(item)).join(", ");
    if (typeof value === "object") return JSON.stringify(localizeData(value));
    return String(value);
  }}

  function escapeHtml(value) {{
    return text(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }}

  function displayText(value) {{
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "boolean") return value ? (valueLabels.true || "true") : (valueLabels.false || "false");
    if (Array.isArray(value)) return value.map((item) => displayText(item)).join(", ");
    if (typeof value === "object") return JSON.stringify(localizeData(value), null, 2);
    const token = String(value);
    return phraseLabels[token] || valueLabels[token] || token;
  }}

  function localizeData(value) {{
    if (value === null || value === undefined || value === "") return value;
    if (typeof value === "boolean") return value ? (valueLabels.true || "true") : (valueLabels.false || "false");
    if (Array.isArray(value)) return value.map((item) => localizeData(item));
    if (typeof value === "object") {{
      return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, localizeData(item)]));
    }}
    const token = String(value);
    return phraseLabels[token] || valueLabels[token] || token;
  }}

  function escapeDisplayHtml(value) {{
    return escapeHtml(displayText(value));
  }}

  function endpointFor(template, candidateId) {{
    return template.replace("{id}", encodeURIComponent(candidateId));
  }}

  function legacyHref(screen, candidateId) {{
    const template = legacyPaths[screen] || legacyPaths.home || "/app/ui";
    return candidateId ? template.replace("{id}", encodeURIComponent(candidateId)) : template;
  }}

  function setStatus(message, kind = "notice") {{
    if (!message) {{
      statusNode.hidden = true;
      statusNode.className = "flash";
      statusNode.textContent = "";
      statusNode.setAttribute("role", "status");
      return;
    }}
    statusNode.hidden = false;
    statusNode.className = kind === "error" ? "flash flash-error" : "flash flash-notice";
    statusNode.setAttribute("role", kind === "error" ? "alert" : "status");
    statusNode.textContent = message;
    statusNode.focus();
  }}

  function setLoading() {{
    root.innerHTML = `<div class="panel"><p class="muted">${{escapeHtml(strings.loading)}}</p></div>`;
  }}

  async function fetchJson(url, options = {{}}) {{
    let response;
    try {{
      response = await fetch(url, {{
        credentials: "same-origin",
        headers: {{
          "Content-Type": "application/json",
          ...(options.headers || {{}}),
        }},
        ...options,
      }});
    }} catch {{
      throw new Error(strings.transportFailure || strings.genericShellFetch || "Request failed.");
    }}
    if (!response.ok) {{
      let detail = strings.genericShellFetch || "Request failed.";
      if (response.status === 401 || response.status === 403) {{
        detail = strings.authFailure || detail;
      }}
      try {{
        const payload = await response.json();
        if (response.status !== 401 && response.status !== 403) {{
          if (typeof payload?.detail === "string") detail = payload.detail;
          else if (payload?.detail?.message) detail = payload.detail.message;
        }}
      }} catch {{}}
      throw new Error(detail);
    }}
    return response.json();
  }}

  function renderCardGrid(cards) {{
    return `<div class="cards">${{cards.map((card) => `
      <section class="card">
        <div class="label">${{escapeHtml(card.key)}}</div>
        <div class="value" style="font-size:1rem;">${{escapeDisplayHtml(card.value)}}</div>
      </section>`).join("")}}</div>`;
  }}

  function localizeSummaryCardKey(key) {{
    if (key === "repository") return strings.repository || "Repository";
    if (key === "reviewable") return strings.reviewable || "Reviewable";
    if (key === "approved_context") return strings.approvedContext || "Approved Context";
    if (key === "blocked_context") return strings.blockedContext || "Blocked Context";
    if (key === "daemon_state") return strings.daemonState || "Daemon State";
    if (key === "next_actions") return strings.nextActions || "Next Actions";
    return key;
  }}

  function localizeFieldKey(key) {{
    return fieldLabels[key] || localizeSummaryCardKey(key) || key.replaceAll("_", " ");
  }}

  function localizeTableLabel(key) {{
    return tableLabels[key] || localizeFieldKey(key) || key;
  }}

  function renderKeyValuePanel(data) {{
    const entries = Object.entries(data || {{}}).filter(([, value]) => value !== null && value !== undefined && value !== "");
    if (!entries.length) return `<p class="muted">${{escapeHtml(strings.emptyPreview)}}</p>`;
    return `<dl class="kv">${{entries.map(([key, value]) => `
      <dt>${{escapeHtml(localizeFieldKey(key))}}</dt><dd>${{escapeDisplayHtml(value)}}</dd>
    `).join("")}}</dl>`;
  }}

  function renderDaemonActions(actions) {{
    if (!actions?.length) return `<p class="muted">${{escapeHtml(strings.emptyNextActions)}}</p>`;
    return `<ul>${{actions.map((action) => `
      <li><strong>${{escapeHtml(action.command || "")}}</strong><br><span class="muted">${{escapeDisplayHtml(action.reason || "")}}</span></li>
    `).join("")}}</ul>`;
  }}

  function renderDecisionValue(column, value) {{
    if (column === "path" || column.endsWith("_path")) return escapeHtml(value);
    return escapeDisplayHtml(value);
  }}

  function renderDecisionRows(decisions, columns, emptyLabel) {{
    if (!decisions.length) return `<tr><td colspan="${{columns.length}}" class="muted">${{escapeHtml(emptyLabel)}}</td></tr>`;
    return decisions.map((decision) => `
      <tr>${{columns.map((column) => `<td>${{renderDecisionValue(column, decision[column] ?? "—")}}</td>`).join("")}}</tr>
    `).join("");
  }}

  function currentScreenLabel() {{
    if (state.screen === "queue") return strings.screenQueue;
    if (state.screen === "detail") return strings.screenDetail;
    if (state.screen === "daemon") return strings.screenDaemon;
    return strings.screenHome;
  }}

  function localizeScreenToken(token) {{
    if (token === "candidate_queue") return strings.screenQueue;
    if (token === "daemon_panel") return strings.screenDaemon;
    if (token === "home") return strings.screenHome;
    return token;
  }}

  function currentJsonSurface() {{
    if (state.screen === "queue") return endpoints.queue;
    if (state.screen === "detail" && state.candidateId) return endpointFor(endpoints.detail, state.candidateId);
    if (state.screen === "daemon") return endpoints.daemon;
    return endpoints.home;
  }}

  function shellHeader() {{
    return `
      <div class="panel">
        <div class="cards">
          <section class="card">
            <div class="label">${{escapeHtml(strings.currentScreen)}}</div>
            <div class="value" style="font-size:1rem;">${{escapeHtml(currentScreenLabel())}}</div>
          </section>
          <section class="card">
            <div class="label">${{escapeHtml(strings.currentTarget)}}</div>
            <div class="value" style="font-size:1rem;">${{escapeHtml(state.candidateId || strings.targetNone)}}</div>
          </section>
          <section class="card">
            <div class="label">${{escapeHtml(strings.jsonSurface)}}</div>
            <div class="detail"><code>${{escapeHtml(currentJsonSurface())}}</code></div>
          </section>
          <section class="card">
            <div class="label">${{escapeHtml(strings.routeState)}}</div>
            <div class="detail">${{escapeHtml(window.location.hash || "#screen=home")}}</div>
          </section>
        </div>
      </div>`;
  }}

  async function logoutSession() {{
    try {{
      await fetchJson(endpoints.logout, {{ method: "POST" }});
      window.location.assign("/app/ui");
    }} catch (error) {{
      setStatus(error.message || strings.genericShellFetch, "error");
    }}
  }}

  function compactCardsFromObject(data, labelMap = {{}}, options = {{}}) {{
    const entries = Object.entries(data || {{}})
      .filter(([, value]) => value !== null && value !== undefined && value !== "");
    if (!entries.length) return `<p class="muted">${{escapeHtml(options.emptyLabel || strings.emptyPreview)}}</p>`;
    return renderCardGrid(entries.map(([key, value]) => ({{
      key: labelMap[key] || localizeFieldKey(key),
      value,
    }})));
  }}

  function renderLineageSummary(lineage) {{
    if (!lineage) return `<p class="muted">${{escapeHtml(strings.emptyLineage)}}</p>`;
    return renderCardGrid([
      {{ key: localizeFieldKey("capture_id"), value: lineage.capture_id }},
      {{ key: localizeFieldKey("status"), value: lineage.status }},
      {{ key: localizeFieldKey("decision"), value: lineage.decision }},
      {{ key: localizeFieldKey("section"), value: lineage.section }},
      {{ key: localizeFieldKey("rde_class"), value: lineage.rde_class }},
      {{ key: localizeFieldKey("events"), value: (lineage.events || []).length }},
    ]);
  }}

  function renderHome() {{
    const homeState = state.homeState || {{ summary_cards: [], top_review_items: [], top_daemon_actions: [] }};
    const quickLinks = (homeState.quick_links || []).map((link) => `
      <li><button type="button" class="link-button" data-open-screen="${{escapeHtml(link.screen)}}">${{escapeHtml(localizeScreenToken(link.screen))}}</button> · <code>${{escapeHtml(link.path || "")}}</code></li>
    `).join("") || `<li class="muted">${{escapeHtml(strings.emptyQuickLinks)}}</li>`;
    const reviewItems = (homeState.top_review_items || []).map((item) => `
      <li>
        <button type="button" class="link-button" data-open-detail="${{escapeHtml(item.candidate_id)}}">${{escapeHtml(item.candidate_id)}}</button>
        · ${{escapeDisplayHtml(item.status)}} · ${{escapeDisplayHtml(item.proposal_section)}}<br>
        <span class="muted">${{escapeHtml(item.display_summary || "")}}</span>
      </li>`).join("") || `<li class="muted">${{escapeHtml(strings.emptyReviewItems)}}</li>`;
    const daemonActions = (homeState.top_daemon_actions || []).map((action) => `
      <li><strong>${{escapeDisplayHtml(action.kind)}}</strong> · ${{escapeDisplayHtml(action.summary || "")}}</li>`).join("") || `<li class="muted">${{escapeHtml(strings.emptyNextActions)}}</li>`;
    root.innerHTML = `
      ${{shellHeader()}}
      <div class="cards">${{(homeState.summary_cards || []).map((card) => `
        <section class="card">
          <div class="label">${{escapeHtml(localizeSummaryCardKey(card.key))}}</div>
          <div class="value">${{escapeDisplayHtml(card.value)}}</div>
        </section>`).join("")}}</div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.captureResult)}}</h3>
          <p class="muted">${{escapeHtml(strings.captureHint)}}</p>
          <form id="resident-shell-capture-form">
            <p><textarea name="content" rows="8" style="width:100%;" placeholder="${{escapeHtml(strings.clipboardPlaceholder)}}"></textarea></p>
            <p><button type="submit">${{escapeHtml(strings.createPendingCandidate)}}</button></p>
          </form>
          <div id="resident-shell-capture-result"></div>
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.quickLinks)}}</h3>
          <ul>${{quickLinks}}</ul>
        </div>
      </div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.queue)}}</h3>
          <ul>${{reviewItems}}</ul>
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.daemon)}}</h3>
          <ul>${{daemonActions}}</ul>
        </div>
      </div>
      <div class="panel">
        <h3>${{escapeHtml(strings.legacySurfaces)}}</h3>
        <p><a href="${{escapeHtml(legacyHref("home"))}}">${{escapeHtml(strings.openLegacyPage)}}: /app/ui</a></p>
      </div>`;
    const form = document.getElementById("resident-shell-capture-form");
    if (form) {{
      form.addEventListener("submit", async (event) => {{
        event.preventDefault();
        const formData = new FormData(form);
        const content = String(formData.get("content") || "").trim();
        if (!content) return;
        setStatus(null);
        const resultNode = document.getElementById("resident-shell-capture-result");
        if (resultNode) resultNode.innerHTML = "";
        try {{
          const payload = await fetchJson(endpoints.capture, {{
            method: "POST",
            body: JSON.stringify({{ content, locale: bootstrap.locale, profile_id: "default" }}),
          }});
          state.lastCapture = payload;
          if (resultNode) {{
            resultNode.innerHTML = `<p><strong>${{escapeHtml(payload.id)}}</strong> · ${{escapeDisplayHtml(payload.status)}}</p>`;
          }}
          form.reset();
          setStatus(strings.noticePendingCandidateCreated || payload.id, "notice");
          await showDetail(payload.id);
        }} catch (error) {{
          setStatus(error.message || strings.genericShellFetch, "error");
        }}
      }});
    }}
    bindDetailButtons();
    bindScreenButtons();
    bindToolbarButtons();
  }}

  function renderQueue() {{
    const queueState = state.queueState || {{ items: [] }};
    const hasQueueState = Boolean(state.queueState);
    const statusCounts = Object.entries(queueState.status_counts || {{}}).map(([status, count]) => `
      <li><strong>${{escapeDisplayHtml(status)}}</strong>: ${{escapeHtml(count)}}</li>
    `).join("") || `<li class="muted">${{escapeHtml(strings.emptyPreview)}}</li>`;
    const topSections = (queueState.top_sections || []).map((item) => `
      <li><strong>${{escapeDisplayHtml(item.section)}}</strong>: ${{escapeHtml(item.count)}}</li>
    `).join("") || `<li class="muted">${{escapeHtml(strings.emptyPreview)}}</li>`;
    const rows = (queueState.items || []).map((item) => `
      <tr>
        <td><button type="button" class="link-button" data-open-detail="${{escapeHtml(item.id)}}">${{escapeHtml(item.id)}}</button></td>
        <td>${{escapeDisplayHtml(item.status)}}</td>
        <td>${{escapeDisplayHtml(item.section)}}</td>
        <td>${{escapeHtml(item.evaluation_level)}} / ${{escapeDisplayHtml(item.rde_class || "—")}}</td>
        <td>${{escapeHtml(item.content_preview)}}</td>
      </tr>`).join("") || `<tr><td colspan="5" class="muted">${{escapeHtml(hasQueueState ? strings.emptyReviewableCandidates : strings.emptyPreview)}}</td></tr>`;
    root.innerHTML = `
      ${{shellHeader()}}
      ${{renderCardGrid([
        {{ key: strings.reviewableCountShort, value: queueState.reviewable_count ?? 0 }},
        {{ key: strings.statusCountsShort, value: Object.keys(queueState.status_counts || {{}}).length }},
        {{ key: strings.topSectionsShort, value: (queueState.top_sections || []).length }},
      ])}}
      <div class="panel">
        <h3>${{escapeHtml(strings.queueSummary)}}</h3>
        <div class="cards">
          <section class="card"><div class="label">${{escapeHtml(strings.statusCountsShort)}}</div><div class="detail"><ul>${{statusCounts}}</ul></div></section>
          <section class="card"><div class="label">${{escapeHtml(strings.topSectionsShort)}}</div><div class="detail"><ul>${{topSections}}</ul></div></section>
        </div>
      </div>
      <div class="panel">
        <p><a href="${{escapeHtml(legacyHref("queue"))}}">${{escapeHtml(strings.openLegacyPage)}}</a></p>
        <div class="shell-table-wrap"><table>
          <thead><tr><th>${{escapeHtml(localizeTableLabel("id"))}}</th><th>${{escapeHtml(localizeTableLabel("status"))}}</th><th>${{escapeHtml(localizeTableLabel("section"))}}</th><th>${{escapeHtml(localizeTableLabel("evaluation"))}}</th><th>${{escapeHtml(localizeTableLabel("preview"))}}</th></tr></thead>
          <tbody>${{rows}}</tbody>
        </table></div>
      </div>`;
    bindDetailButtons();
    bindToolbarButtons();
  }}

  function renderDetail() {{
    const detail = state.detailState;
    if (!detail) {{
      root.innerHTML = `<div class="panel"><p class="muted">${{escapeHtml(strings.detailUnavailable)}}</p></div>`;
      return;
    }}
    const allowed = detail.allowed_actions || {{}};
    const disabledAttr = (allowedValue) => allowedValue ? "" : " disabled";
    const actionHint = (allowedValue) => allowedValue ? "" : `<p class="muted">${{escapeHtml(strings.actionUnavailable)}}</p>`;
    const evaluateLevel = detail.ui_summary?.evaluation_level || 1;
    const currentSection = detail.ui_summary?.section || "";
    const detailSummaryHtml = compactCardsFromObject(detail.ui_summary, {{}}, {{ emptyLabel: strings.emptyPreview }});
    const proposalSummaryHtml = compactCardsFromObject(detail.proposal, {{}}, {{ emptyLabel: strings.emptyPreview }});
    const evaluationSummaryHtml = compactCardsFromObject(detail.evaluation, {{}}, {{ emptyLabel: strings.emptyPreview }});
    const diffSummaryHtml = state.detailDiff?.ui_summary
      ? compactCardsFromObject(state.detailDiff.ui_summary, {{}}, {{ emptyLabel: strings.emptyDiffSummary }})
      : `<p class="muted">${{escapeHtml(strings.loading)}}</p>`;
    const diffHtml = state.detailDiff
      ? `<pre>${{escapeHtml(JSON.stringify(localizeData(state.detailDiff), null, 2))}}</pre>`
      : `<p class="muted">${{escapeHtml(strings.loading)}}</p>`;
    const lineageEvents = (state.detailLineage?.events || []).map((event) => `
      <li><strong>${{escapeHtml(event.operation)}}</strong> · ${{escapeHtml(event.timestamp)}} · ${{escapeHtml(event.node_kind || "")}}${{event.note ? ` · ${{escapeHtml(event.note)}}` : ""}}</li>
    `).join("") || `<li class="muted">${{escapeHtml(strings.emptyLineage)}}</li>`;
    root.innerHTML = `
      ${{shellHeader()}}
      <div class="panel">
        <p>
          <button type="button" data-shell-nav="queue">${{escapeHtml(strings.backToQueue)}}</button>
          <a href="${{escapeHtml(legacyHref("detail", state.candidateId))}}">${{escapeHtml(strings.openLegacyPage)}}</a>
        </p>
        <p><strong>${{escapeHtml(localizeFieldKey("id"))}}:</strong> ${{escapeHtml(state.candidateId || "")}}</p>
        <p><strong>${{escapeHtml(localizeFieldKey("status"))}}:</strong> ${{escapeDisplayHtml(detail.ui_summary?.status)}}</p>
        <p><strong>${{escapeHtml(localizeFieldKey("section"))}}:</strong> ${{escapeDisplayHtml(detail.ui_summary?.section)}}</p>
        <p><strong>${{escapeHtml(localizeFieldKey("source_type"))}}:</strong> ${{escapeDisplayHtml(detail.ui_summary?.source_type)}}</p>
        <div class="boundary">${{escapeHtml(detail.ui_summary?.action_guidance || "")}}</div>
      </div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.detailSummary)}}</h3>
          ${{detailSummaryHtml}}
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.proposalSummary)}}</h3>
          ${{proposalSummaryHtml}}
        </div>
      </div>
      <div class="panel">
        <h3>${{escapeHtml(strings.evaluationSummaryCards)}}</h3>
        ${{evaluationSummaryHtml}}
      </div>
      <div class="panel">
        <h3>${{escapeHtml(strings.content)}}</h3>
        <pre>${{escapeHtml(detail.content || "")}}</pre>
      </div>
      <div class="panel">
        <h3>${{escapeHtml(strings.actions)}}</h3>
        <div class="resident-shell-toolbar">
          <button type="button" data-open-action-form="evaluate"${{disabledAttr(allowed.evaluate)}}>${{escapeHtml(strings.evaluate)}}</button>
          <button type="button" data-open-action-form="approve"${{disabledAttr(allowed.approve)}}>${{escapeHtml(strings.approve)}}</button>
          <button type="button" data-open-action-form="reject"${{disabledAttr(allowed.reject)}}>${{escapeHtml(strings.reject)}}</button>
          <button type="button" data-open-action-form="revise"${{disabledAttr(allowed.revise)}}>${{escapeHtml(strings.createRevisedCandidate)}}</button>
        </div>
      </div>
      <div class="panel">
        <h3>${{escapeHtml(strings.actionForms)}}</h3>
        <div class="shell-action-grid">
          <form id="resident-shell-evaluate-form" class="shell-form-grid" hidden>
            <label for="resident-shell-evaluate-level">${{escapeHtml(strings.evaluateLevel)}}</label>
            <input id="resident-shell-evaluate-level" name="level" type="number" min="1" max="3" value="${{escapeHtml(evaluateLevel)}}">
            <button type="submit"${{disabledAttr(allowed.evaluate)}}>${{escapeHtml(strings.evaluate)}}</button>
            ${{actionHint(allowed.evaluate)}}
          </form>
          <form id="resident-shell-approve-form" class="shell-form-grid" hidden>
            <label for="resident-shell-approve-override">${{escapeHtml(strings.overrideReason)}}</label>
            <input id="resident-shell-approve-override" name="override_reason" type="text">
            <label><input id="resident-shell-approve-force-critical" name="force_critical" type="checkbox"> ${{escapeHtml(strings.forceCriticalApprove)}}</label>
            <button type="submit"${{disabledAttr(allowed.approve)}}>${{escapeHtml(strings.approve)}}</button>
            ${{actionHint(allowed.approve)}}
          </form>
          <form id="resident-shell-reject-form" class="shell-form-grid" hidden>
            <label for="resident-shell-reject-reason">${{escapeHtml(strings.rejectReason)}}</label>
            <input id="resident-shell-reject-reason" name="reason" type="text">
            <button type="submit"${{disabledAttr(allowed.reject)}}>${{escapeHtml(strings.reject)}}</button>
            ${{actionHint(allowed.reject)}}
          </form>
          <form id="resident-shell-revise-form" class="shell-form-grid" hidden>
            <label for="resident-shell-revise-content">${{escapeHtml(strings.revisedContent)}}</label>
            <textarea id="resident-shell-revise-content" name="edited_text" rows="8">${{escapeHtml(detail.content || "")}}</textarea>
            <label for="resident-shell-revise-section">${{escapeHtml(strings.targetSection)}}</label>
            <input id="resident-shell-revise-section" name="target_section" type="text" value="${{escapeHtml(currentSection)}}">
            <label for="resident-shell-revise-reason">${{escapeHtml(strings.changeReason)}}</label>
            <input id="resident-shell-revise-reason" name="change_reason" type="text">
            <button type="submit"${{disabledAttr(allowed.revise)}}>${{escapeHtml(strings.createRevisedCandidate)}}</button>
            ${{actionHint(allowed.revise)}}
          </form>
        </div>
      </div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.diffSummaryCards)}}</h3>
          ${{diffSummaryHtml}}
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.lineageSummary)}}</h3>
          ${{renderLineageSummary(state.detailLineage)}}
        </div>
      </div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.diffInspection)}}</h3>
          <p><a href="${{escapeHtml(legacyHref("diff", state.candidateId))}}">${{escapeHtml(strings.openLegacyPage)}}</a></p>
          ${{diffHtml}}
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.lineageEvents)}}</h3>
          <ul>${{lineageEvents}}</ul>
        </div>
      </div>`;
    bindDetailActionButtons();
    bindToolbarButtons();
  }}

  function renderDaemon() {{
    const daemon = state.daemonState || {{ summary_cards: [] }};
    const runtimeInit = daemon.runtime_init || {{}};
    const cleanupPreview = daemon.cleanup_preview || {{}};
    const repairPreview = daemon.repair_preview || {{}};
    const packagingStatus = daemon.packaging_status || {{}};
    const serviceControlBoundary = daemon.service_control_boundary || {{}};
    const supervisionStatus = daemon.supervision_status || {{}};
    const recoveryConsentStatus = daemon.recovery_consent_status || {{}};
    const serviceTargetsStatus = daemon.service_targets_status || {{}};
    const launchagentPreview = daemon.launchagent_preview || null;
    const launchagentStatus = daemon.launchagent_status || null;
    const cleanupReport = cleanupPreview.decision_report || {{}};
    const cleanupDecisions = (cleanupReport.decisions || []).map((decision) => ({{
      artifact_kind: decision.artifact_kind,
      diagnostic_status: decision.diagnostic_status,
      recommendation: decision.recommendation,
      reason: decision.reason,
    }}));
    const repairDecisions = Object.entries(repairPreview.decisions || {{}}).map(([target, item]) => ({{
      target,
      status: item?.status,
      repairable: item?.repairable,
      path: item?.path,
    }}));
    const runtimeItems = (runtimeInit.items || []).map((item) => ({{
      path_role: item.path_role,
      status: item.status,
      path: item.path,
      reason: item.reason,
    }}));
    const serviceTargetRows = (serviceTargetsStatus.targets || []).map((item) => ({{
      target: item.target,
      platform: item.platform,
      service_manager: item.service_manager,
      status: item.status,
    }}));
    const allowedControlCommands = (serviceControlBoundary.control_plane?.allowed_commands || []).map((item) => item.command);
    const allowedServiceCommands = (serviceControlBoundary.service_plane?.allowed_commands || []).map((item) => item.command);
    const deferredServiceCommands = serviceControlBoundary.service_plane?.deferred_commands || [];
    const supervisionActions = supervisionStatus.active_supervision?.allowed_actions || [];
    const recoveryFlow = recoveryConsentStatus.recommended_recovery_flow || [];
    root.innerHTML = `
      ${{shellHeader()}}
      ${{renderCardGrid((daemon.summary_cards || []).map((card) => ({{
        key:
          card.key === "state" ? strings.daemonState :
          card.key === "is_running_daemon" ? strings.running :
          card.key === "runtime_initialized" ? strings.runtimeInitialized :
          card.key === "readiness_status" ? strings.readiness :
          card.key,
        value: card.value,
      }}))}}
      <div class="panel">
        <p><a href="${{escapeHtml(legacyHref("daemon"))}}">${{escapeHtml(strings.openLegacyPage)}}</a></p>
        <h3>${{escapeHtml(strings.nextActions)}}</h3>
        ${{renderDaemonActions(daemon.next_actions || [])}}
      </div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.runtimeInitPreview)}}</h3>
          ${{renderKeyValuePanel({{
          kind: runtimeInit.kind,
          operation_id: runtimeInit.operation_id,
          plan_fingerprint: runtimeInit.plan_fingerprint,
          review_required: runtimeInit.review_required,
          operator_confirmation_signal: runtimeInit.operator_confirmation_signal,
          metadata_path: runtimeInit.metadata_path,
        }})}}
        <div class="shell-table-wrap"><table class="compact-table">
          <thead><tr><th>${{escapeHtml(localizeTableLabel("role"))}}</th><th>${{escapeHtml(localizeTableLabel("status"))}}</th><th>${{escapeHtml(localizeTableLabel("path"))}}</th><th>${{escapeHtml(localizeTableLabel("reason"))}}</th></tr></thead>
          <tbody>${{renderDecisionRows(runtimeItems, ["path_role", "status", "path", "reason"], strings.emptyPreview)}}</tbody>
        </table></div>
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.cleanupPreview)}}</h3>
          ${{renderKeyValuePanel({{
          kind: cleanupPreview.kind,
          operation_id: cleanupPreview.operation_id,
          preview_hash: cleanupPreview.preview_hash,
          allowed_targets: text(cleanupPreview.allowed_targets || []),
          decision_policy: cleanupReport.decision_policy,
          manual_review_required: cleanupReport.manual_review_required,
        }})}}
        <div class="shell-table-wrap"><table class="compact-table">
          <thead><tr><th>${{escapeHtml(localizeTableLabel("artifact"))}}</th><th>${{escapeHtml(localizeTableLabel("status"))}}</th><th>${{escapeHtml(localizeTableLabel("recommendation"))}}</th><th>${{escapeHtml(localizeTableLabel("reason"))}}</th></tr></thead>
          <tbody>${{renderDecisionRows(cleanupDecisions, ["artifact_kind", "diagnostic_status", "recommendation", "reason"], strings.emptyPreview)}}</tbody>
        </table></div>
        </div>
      </div>
      <div class="panel">
        <h3>${{escapeHtml(strings.repairPreview)}}</h3>
        ${{renderKeyValuePanel({{
          kind: repairPreview.kind,
          operation_id: repairPreview.operation_id,
          preview_hash: repairPreview.preview_hash,
          allowed_targets: text(repairPreview.allowed_targets || []),
        }})}}
        <div class="shell-table-wrap"><table class="compact-table">
          <thead><tr><th>${{escapeHtml(localizeTableLabel("target"))}}</th><th>${{escapeHtml(localizeTableLabel("status"))}}</th><th>${{escapeHtml(localizeTableLabel("repairable"))}}</th><th>${{escapeHtml(localizeTableLabel("path"))}}</th></tr></thead>
          <tbody>${{renderDecisionRows(repairDecisions, ["target", "status", "repairable", "path"], strings.emptyPreview)}}</tbody>
        </table></div>
      </div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.packagingStatus)}}</h3>
          ${{renderKeyValuePanel({{
            kind: packagingStatus.kind,
            packaging_model: packagingStatus.packaging_model,
            supervision_model: packagingStatus.supervision_model,
            phase_status: packagingStatus.phase_status,
          }})}}
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.serviceControlBoundary)}}</h3>
          ${{renderKeyValuePanel({{
            kind: serviceControlBoundary.kind,
            control_plane_status: serviceControlBoundary.control_plane?.status,
            service_plane_status: serviceControlBoundary.service_plane?.status,
          }})}}
          <h4>${{escapeHtml(strings.allowedCommands)}}</h4>
          <ul>${{[...allowedControlCommands, ...allowedServiceCommands].map((command) => `<li><code>${{escapeHtml(command)}}</code></li>`).join("") || `<li class="muted">${{escapeHtml(strings.emptyPreview)}}</li>`}}</ul>
          <h4>${{escapeHtml(strings.deferredCommands)}}</h4>
          <ul>${{deferredServiceCommands.map((command) => `<li><code>${{escapeHtml(command)}}</code></li>`).join("") || `<li class="muted">${{escapeHtml(strings.emptyPreview)}}</li>`}}</ul>
        </div>
      </div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.supervisionStatus)}}</h3>
          ${{renderKeyValuePanel({{
            kind: supervisionStatus.kind,
            supervision_mode: supervisionStatus.supervision_mode,
            phase_status: supervisionStatus.phase_status,
            active_supervision_status: supervisionStatus.active_supervision?.status,
          }})}}
          <h4>${{escapeHtml(strings.allowedCommands)}}</h4>
          <ul>${{supervisionActions.map((command) => `<li><code>${{escapeHtml(command)}}</code></li>`).join("") || `<li class="muted">${{escapeHtml(strings.emptyPreview)}}</li>`}}</ul>
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.recoveryConsentStatus)}}</h3>
          ${{renderKeyValuePanel({{
            kind: recoveryConsentStatus.kind,
            consent_model: recoveryConsentStatus.consent_model,
            recovery_model: recoveryConsentStatus.recovery_model,
            phase_status: recoveryConsentStatus.phase_status,
          }})}}
          <h4>${{escapeHtml(strings.recommendedFlow)}}</h4>
          <ul>${{recoveryFlow.map((item) => `<li>${{escapeHtml(item)}}</li>`).join("") || `<li class="muted">${{escapeHtml(strings.emptyPreview)}}</li>`}}</ul>
        </div>
      </div>
      <div class="shell-grid two-up">
        <div class="panel">
          <h3>${{escapeHtml(strings.serviceTargets)}}</h3>
          ${{renderKeyValuePanel({{
            kind: serviceTargetsStatus.kind,
            current_platform: serviceTargetsStatus.current_platform,
            recommended_target: serviceTargetsStatus.recommended_target,
          }})}}
          <div class="shell-table-wrap"><table class="compact-table">
            <thead><tr><th>${{escapeHtml(localizeTableLabel("target"))}}</th><th>Platform</th><th>Service Manager</th><th>${{escapeHtml(localizeTableLabel("status"))}}</th></tr></thead>
            <tbody>${{renderDecisionRows(serviceTargetRows, ["target", "platform", "service_manager", "status"], strings.emptyPreview)}}</tbody>
          </table></div>
        </div>
        <div class="panel">
          <h3>${{escapeHtml(strings.launchagentPreview)}}</h3>
          ${{launchagentPreview ? renderKeyValuePanel({{
            kind: launchagentPreview.kind,
            operation_id: launchagentPreview.operation_id,
            preview_hash: launchagentPreview.preview_hash,
            label: launchagentPreview.label,
            plist_path: launchagentPreview.plist_path,
          }}) : `<p class="muted">${{escapeHtml(strings.emptyPreview)}}</p>`}}
          ${{launchagentPreview?.launchctl_commands ? `<ul>${{Object.entries(launchagentPreview.launchctl_commands).map(([name, command]) => `<li><strong>${{escapeHtml(name)}}</strong>: <code>${{escapeHtml(command)}}</code></li>`).join("")}}</ul>` : ""}}
        </div>
      </div>
      <div class="panel">
        <h3>${{escapeHtml(strings.launchagentStatus)}}</h3>
        ${{launchagentStatus ? renderKeyValuePanel({{
          kind: launchagentStatus.kind,
          label: launchagentStatus.label,
          plist_path: launchagentStatus.plist_path,
          plist_exists: launchagentStatus.plist_exists,
          loaded_status: launchagentStatus.loaded_status,
          service_manager: launchagentStatus.service_manager,
        }}) : `<p class="muted">${{escapeHtml(strings.emptyPreview)}}</p>`}}
      </div>
      <div class="panel">
        <h3>${{escapeHtml(strings.daemonObservation)}}</h3>
        <pre>${{escapeHtml(JSON.stringify(localizeData(daemon), null, 2))}}</pre>
      </div>`;
    bindToolbarButtons();
  }}

  function bindDetailButtons() {{
    root.querySelectorAll("[data-open-detail]").forEach((node) => {{
      node.addEventListener("click", () => {{
        const candidateId = node.getAttribute("data-open-detail");
        if (candidateId) void showDetail(candidateId);
      }});
    }});
  }}

  function bindScreenButtons() {{
    root.querySelectorAll("[data-open-screen]").forEach((node) => {{
      node.addEventListener("click", () => {{
        const screen = node.getAttribute("data-open-screen");
        if (screen === "candidate_queue") void showQueue();
        else if (screen === "daemon_panel") void showDaemon();
      }});
    }});
  }}

  function bindToolbarButtons() {{
    document.querySelectorAll("[data-shell-nav]").forEach((node) => {{
      const screen = node.getAttribute("data-shell-nav");
      const active =
        (screen === "home" && state.screen === "home") ||
        (screen === "queue" && state.screen === "queue") ||
        (screen === "daemon" && state.screen === "daemon");
      node.classList.toggle("shell-nav-active", Boolean(active));
      node.addEventListener("click", () => {{
        const nextScreen = node.getAttribute("data-shell-nav");
        if (nextScreen === "queue") void showQueue();
        else if (nextScreen === "daemon") void showDaemon();
        else void showHome();
      }});
    }});
    document.querySelectorAll("[data-shell-refresh]").forEach((node) => {{
      node.addEventListener("click", () => void refreshVisibleState());
    }});
    document.querySelectorAll("[data-shell-logout]").forEach((node) => {{
      node.addEventListener("click", () => void logoutSession());
    }});
  }}

  function bindDetailActionButtons() {{
    const forms = ["evaluate", "approve", "reject", "revise"];
    function toggleActionForm(kind) {{
      forms.forEach((name) => {{
        const form = document.getElementById(`resident-shell-${{name}}-form`);
        if (form) form.hidden = name !== kind;
      }});
    }}
    root.querySelectorAll("[data-open-action-form]").forEach((node) => {{
      node.addEventListener("click", () => {{
        const action = node.getAttribute("data-open-action-form");
        if (action) toggleActionForm(action);
      }});
    }});
    const evaluateForm = document.getElementById("resident-shell-evaluate-form");
    if (evaluateForm) {{
      evaluateForm.addEventListener("submit", async (event) => {{
        event.preventDefault();
        if (!state.candidateId) return;
        try {{
          const level = Number(document.getElementById("resident-shell-evaluate-level")?.value || "1");
          await fetchJson(endpointFor(endpoints.evaluate, state.candidateId), {{
            method: "POST",
            body: JSON.stringify({{ level }}),
          }});
          await showDetail(state.candidateId);
          setStatus(strings.noticeCandidateEvaluated, "notice");
        }} catch (error) {{
          setStatus(error.message || strings.genericShellFetch, "error");
        }}
      }});
    }}
    const approveForm = document.getElementById("resident-shell-approve-form");
    if (approveForm) {{
      approveForm.addEventListener("submit", async (event) => {{
        event.preventDefault();
        if (!state.candidateId) return;
        try {{
          const overrideReason = document.getElementById("resident-shell-approve-override")?.value || "";
          const forceCritical = Boolean(document.getElementById("resident-shell-approve-force-critical")?.checked);
          await fetchJson(endpointFor(endpoints.approve, state.candidateId), {{
            method: "POST",
            body: JSON.stringify({{
              force_critical: forceCritical,
              override_reason: overrideReason || null,
            }}),
          }});
          await showQueue();
          setStatus(strings.noticeCandidateApproved, "notice");
        }} catch (error) {{
          setStatus(error.message || strings.genericShellFetch, "error");
        }}
      }});
    }}
    const rejectForm = document.getElementById("resident-shell-reject-form");
    if (rejectForm) {{
      rejectForm.addEventListener("submit", async (event) => {{
        event.preventDefault();
        if (!state.candidateId) return;
        try {{
          const reason = document.getElementById("resident-shell-reject-reason")?.value || "";
          await fetchJson(endpointFor(endpoints.reject, state.candidateId), {{
            method: "POST",
            body: JSON.stringify({{ reason: reason || null }}),
          }});
          await showQueue();
          setStatus(strings.noticeCandidateRejected, "notice");
        }} catch (error) {{
          setStatus(error.message || strings.genericShellFetch, "error");
        }}
      }});
    }}
    const reviseForm = document.getElementById("resident-shell-revise-form");
    if (reviseForm) {{
      reviseForm.addEventListener("submit", async (event) => {{
        event.preventDefault();
        if (!state.candidateId) return;
        try {{
          const editedText = document.getElementById("resident-shell-revise-content")?.value || "";
          const targetSection = document.getElementById("resident-shell-revise-section")?.value || "";
          const changeReason = document.getElementById("resident-shell-revise-reason")?.value || "";
          const payload = await fetchJson(endpointFor(endpoints.revise, state.candidateId), {{
            method: "POST",
            body: JSON.stringify({{
              edited_text: editedText,
              target_section: targetSection || null,
              change_reason: changeReason || null,
            }}),
          }});
          await showDetail(payload.id);
          setStatus(strings.noticeRevisedCandidateCreated, "notice");
        }} catch (error) {{
          setStatus(error.message || strings.genericShellFetch, "error");
        }}
      }});
    }}
  }}

  async function showHome() {{
    state.screen = "home";
    state.candidateId = null;
    syncRouteHash();
    setLoading();
    try {{
      state.homeState = await fetchJson(endpoints.home);
      renderHome();
    }} catch (error) {{
      setStatus(error.message || strings.genericShellFetch, "error");
      renderHome();
    }}
  }}

  async function showQueue() {{
    state.screen = "queue";
    state.candidateId = null;
    syncRouteHash();
    setLoading();
    try {{
      state.queueState = await fetchJson(endpoints.queue);
      renderQueue();
    }} catch (error) {{
      state.queueState = {{
        items: [],
        reviewable_count: 0,
        status_counts: {{}},
        top_sections: [],
      }};
      setStatus(error.message || strings.genericShellFetch, "error");
      renderQueue();
    }}
  }}

  async function showDetail(candidateId) {{
    state.screen = "detail";
    state.candidateId = candidateId;
    syncRouteHash();
    setLoading();
    try {{
      const [detailState, detailDiff, detailLineage] = await Promise.all([
        fetchJson(endpointFor(endpoints.detail, candidateId)),
        fetchJson(endpointFor(endpoints.diff, candidateId)),
        fetchJson(endpointFor(endpoints.lineage, candidateId)),
      ]);
      state.detailState = detailState;
      state.detailDiff = detailDiff;
      state.detailLineage = detailLineage;
      renderDetail();
    }} catch (error) {{
      setStatus(error.message || strings.fallbackQueueError, "error");
      await showQueue();
    }}
  }}

  async function showDaemon() {{
    state.screen = "daemon";
    state.candidateId = null;
    syncRouteHash();
    setLoading();
    try {{
      state.daemonState = await fetchJson(endpoints.daemon);
      renderDaemon();
    }} catch (error) {{
      state.daemonState = {{
        summary_cards: [],
        next_actions: [],
        runtime_init: {{}},
        cleanup_preview: {{}},
        repair_preview: {{}},
      }};
      setStatus(error.message || strings.genericShellFetch, "error");
      renderDaemon();
    }}
  }}

  async function refreshVisibleState() {{
    if (state.screen === "queue") await showQueue();
    else if (state.screen === "detail" && state.candidateId) await showDetail(state.candidateId);
    else if (state.screen === "daemon") await showDaemon();
    else await showHome();
  }}

  async function restoreRouteState() {{
    const route = parseRouteHash();
    if (route.screen === "detail" && route.candidateId) {{
      await showDetail(route.candidateId);
      return;
    }}
    if (route.screen === "queue") {{
      await showQueue();
      return;
    }}
    if (route.screen === "daemon") {{
      await showDaemon();
      return;
    }}
    await showHome();
  }}

  window.addEventListener("hashchange", () => {{
    void restoreRouteState();
  }});

  bindToolbarButtons();
  void restoreRouteState();
}})();
</script>
</section>
"""


def render_resident_app_home(
    contract: dict[str, Any],
    overview: dict[str, Any],
    *,
    locale: str = DEFAULT_BOOTSTRAP_LOCALE,
    notice: str | None = None,
    error: str | None = None,
) -> str:
    summary = overview["summary"]
    review_summary = overview["review_summary"]
    daemon_summary = overview["daemon_summary"]
    read_surfaces = contract.get("read_surfaces", [])

    top_items = review_summary.get("top_items", [])
    review_items_html = (
        "".join(
            (
                "<li>"
                f'<a href="/app/ui/candidates/{escape(item["candidate_id"])}"><strong>{escape(item["candidate_id"])}</strong></a> · '
                f'{escape(_translate_display_token(item["status"], locale))} · '
                f'{escape(_translate_display_token(item["proposal_section"], locale))}<br>'
                f'<span class="muted">{escape(item["display_summary"])}</span>'
                "</li>"
            )
            for item in top_items
        )
        if top_items
        else f'<li class="muted">{escape(_copy("empty.reviewable_candidates", locale))}</li>'
    )

    top_actions = daemon_summary.get("top_next_actions", [])
    daemon_actions_html = (
        "".join(
            (
                "<li>"
                f'<strong>{escape(_translate_display_token(action.get("kind", "action"), locale))}</strong> · '
                f'{escape(_translate_display_phrase(action.get("summary", ""), locale))}'
                "</li>"
            )
            for action in top_actions
        )
        if top_actions
        else f'<li class="muted">{escape(_copy("empty.immediate_daemon_actions", locale))}</li>'
    )

    read_surface_html = "".join(
        (
            "<li>"
            f'<code>{escape(surface["path"])}</code>'
            f' — {escape(_translate_read_surface_purpose(surface["purpose"], locale))}'
            "</li>"
        )
        for surface in read_surfaces
    )
    overview_cards = _render_cards_grid([
        _render_card(_copy("label.repository", locale), _copy("detail.repository_available", locale) if summary["repository_available"] else _copy("detail.repository_unavailable", locale)),
        _render_card(_copy("label.reviewable", locale), summary["reviewable_count"], _copy("detail.home_reviewable", locale)),
        _render_card(_copy("label.approved_context", locale), summary["approved_context_count"], _copy("detail.home_approved_context", locale)),
        _render_card(_copy("label.blocked_context", locale), summary["blocked_context_count"], _copy("detail.home_blocked_context", locale)),
        _render_card(_copy("label.daemon_state", locale), _translate_display_token(summary["daemon_state"], locale), f'{_copy("detail.readiness_prefix", locale)}: {_translate_display_token(summary["readiness_status"], locale)}'),
        _render_card(_copy("label.next_actions", locale), summary["next_action_count"], _copy("detail.home_next_actions", locale)),
    ])
    review_items_panel = _render_panel_without_title(f"<ul>{review_items_html}</ul>")
    daemon_actions_panel = _render_panel_without_title(
        f'<ul>{daemon_actions_html}</ul><p><a href="/app/ui/daemon">{escape(_copy("action.open_daemon_panel", locale))}</a></p>'
    )
    bootstrap_contract_panel = _render_panel_without_title(
        f"<p><strong>{escape(_copy('label.preferred_entrypoint', locale))}:</strong> <code>{escape(contract['preferred_entrypoint'])}</code></p><ul>{read_surface_html}</ul>"
    )
    clipboard_form_panel = _render_panel_without_title(
        f"""
<form method="post" action="/app/ui/capture-clipboard">
<p><label for="capture-content"><strong>Content</strong></label></p>
<p><textarea id="capture-content" name="content" rows="8" style="width:100%;" placeholder="Paste clipboard text here"></textarea></p>
<p><label for="capture-locale">Locale</label> <input id="capture-locale" name="locale" value="{escape(locale)}"></p>
<p><button type="submit">Create pending candidate</button></p>
</form>
"""
    )
    clipboard_form_panel = (
        clipboard_form_panel
        .replace(">Content<", f">{escape(_copy('label.content_field', locale))}<")
        .replace('placeholder="Paste clipboard text here"', f'placeholder="{escape(_copy("placeholder.clipboard", locale))}"')
        .replace(">Locale<", f">{escape(_copy('label.locale', locale))}<")
        .replace(">Create pending candidate<", f">{escape(_copy('action.create_pending_candidate', locale))}<")
    )
    shell_panel = _render_resident_app_shell_bootstrap(contract, overview, locale=locale)

    body = f"""
<header>
<h1>{escape(_copy("heading.home", locale))}</h1>
<p class="muted">{escape(_copy("desc.home", locale))}</p>
</header>
<section>
<h2>{escape(_copy("label.overview", locale))}</h2>
{overview_cards}
</section>
<section>
<h2>{escape(_copy("label.top_review_items", locale))}</h2>
{review_items_panel}
</section>
<section>
<h2>{escape(_copy("label.daemon_next_actions", locale))}</h2>
{daemon_actions_panel}
</section>
<section>
<h2>{escape(_copy("label.bootstrap_contract", locale))}</h2>
{bootstrap_contract_panel}
</section>
<section>
<h2>{escape(_copy("label.clipboard_capture", locale))}</h2>
{clipboard_form_panel}
</section>
{shell_panel}
<div class="boundary">
<strong>{escape(_copy("boundary.label", locale))}:</strong> {escape(_copy("desc.boundary", locale))}
</div>
"""
    return _page(_copy("title.home", locale), body, locale=locale, notice=notice, error=error)


def render_resident_app_candidate_queue(
    payload: dict[str, Any],
    *,
    locale: str = DEFAULT_BOOTSTRAP_LOCALE,
    notice: str | None = None,
    error: str | None = None,
) -> str:
    items = payload.get("items", [])
    pending_count = sum(1 for item in items if item.get("status") == "pending")
    evaluated_count = sum(1 for item in items if item.get("status") == "evaluated")
    status_counts = payload.get("status_counts", {})
    top_sections = payload.get("top_sections", [])
    status_counts_html = "".join(
        f"<li><strong>{escape(_translate_display_token(status, locale))}</strong>: {escape(str(count))}</li>"
        for status, count in status_counts.items()
    ) or f'<li class="muted">{escape(_copy("empty.queue_status_summary", locale))}</li>'
    top_sections_html = "".join(
        f"<li><strong>{escape(_translate_display_token(section.get('section', ''), locale))}</strong>: {escape(str(section.get('count', 0)))}</li>"
        for section in top_sections
    ) or f'<li class="muted">{escape(_copy("empty.section_summary", locale))}</li>'
    item_html = "".join(
        (
            "<tr>"
            f'<td><a href="/app/ui/candidates/{escape(item["id"])}">{escape(item["id"])}</a></td>'
            f'<td><span class="pill pill-{escape(item.get("status", ""))}">{escape(_translate_display_token(item.get("status", ""), locale))}</span></td>'
            f'<td>{escape(_translate_display_token(item.get("section", ""), locale))}</td>'
            f'<td>{escape(str(item.get("evaluation_level", "")) if item.get("evaluation_level") is not None else "-")} / {escape(_translate_display_token(item.get("rde_class", ""), locale) if item.get("rde_class") else _copy("detail.not_evaluated_short", locale))}</td>'
            f'<td>{escape(item.get("content_preview", ""))}</td>'
            "</tr>"
        )
        for item in items
    ) or f'<tr><td colspan="5" class="muted">{escape(_copy("empty.reviewable_candidates", locale))}</td></tr>'
    queue_summary_cards = _render_cards_grid([
        _render_card(_copy("label.queue_status_counts", locale), "", f"<ul>{status_counts_html}</ul>", detail_is_html=True),
        _render_card(_copy("label.top_sections", locale), "", f"<ul>{top_sections_html}</ul>", detail_is_html=True),
    ])

    body = f"""
<h1>{escape(_copy("heading.queue", locale))}</h1>
<p class="muted">{escape(_copy("desc.queue", locale))}</p>
<p><strong>{escape(_copy("label.reviewable_count", locale))}:</strong> {escape(str(payload.get("reviewable_count", 0)))}</p>
<p><strong>{escape(_copy("label.pending", locale))}:</strong> {pending_count} · <strong>{escape(_copy("label.evaluated", locale))}:</strong> {evaluated_count}</p>
{queue_summary_cards}
<table>
<thead><tr><th>{escape(_copy("table.id", locale))}</th><th>{escape(_copy("table.status", locale))}</th><th>{escape(_copy("table.section", locale))}</th><th>{escape(_copy("table.evaluation", locale))}</th><th>{escape(_copy("table.preview", locale))}</th></tr></thead>
<tbody>{item_html}</tbody>
</table>
"""
    return _page(_copy("title.queue", locale), body, locale=locale, notice=notice, error=error)


def render_resident_app_candidate_detail(
    candidate: dict[str, Any],
    diff_path: str,
    *,
    locale: str = DEFAULT_BOOTSTRAP_LOCALE,
    notice: str | None = None,
    error: str | None = None,
) -> str:
    proposal = candidate.get("proposal", {})
    evaluation = candidate.get("evaluation") or {}
    source = candidate.get("source") or {}
    status_value = str(candidate.get("status", ""))
    evaluation_summary = (
        f'{escape(_copy("detail.level_prefix", locale))} {escape(str(evaluation.get("level")))} / {escape(_translate_display_token(evaluation.get("rde_class"), locale))}'
        if evaluation.get("level") is not None and evaluation.get("rde_class")
        else _copy("detail.not_evaluated_yet", locale)
    )
    guidance = ""
    if status_value != "evaluated":
        guidance = (
            f'<div class="panel"><span class="pill pill-warning">{escape(_copy("detail.action_guidance", locale))}</span> '
            f"{escape(_copy('detail.action_guidance_pending', locale))}"
            "</div>"
        )
    elif evaluation.get("rde_class"):
        guidance = (
        f'<div class="panel"><span class="pill pill-evaluated">{escape(_copy("detail.rde_evaluated", locale))}</span> '
            f'{escape(_copy("detail.rde_class_prefix", locale))}: {escape(_translate_display_token(evaluation.get("rde_class"), locale))}'
            "</div>"
        )
    detail_meta_panel = _render_panel_without_title(
        f"""
<strong>{escape(_translate_display_key("id", locale))}:</strong> {escape(candidate.get("id", ""))}<br>
<strong>{escape(_translate_display_key("status", locale))}:</strong> <span class="pill pill-{escape(status_value)}">{escape(_translate_display_token(status_value, locale))}</span><br>
<strong>{escape(_translate_display_key("section", locale))}:</strong> {escape(_translate_display_token(proposal.get("section", ""), locale))}<br>
<strong>{escape(_translate_display_key("source", locale))}:</strong> {escape(_translate_display_token(source.get("type", ""), locale))}
"""
    )
    detail_cards = _render_cards_grid([
        _render_card(_copy("label.evaluation_summary", locale), evaluation_summary, value_font_size="1rem"),
        _render_card(_copy("label.operation", locale), _translate_display_token(proposal.get("operation", ""), locale), value_font_size="1rem"),
    ])
    content_panel = _render_panel(_copy("label.content", locale), f"<pre>{escape(candidate.get('content', ''))}</pre>")
    actions_panel = _render_panel(
        _copy("label.actions", locale),
        f"""
<form method="post" action="/app/ui/candidates/{escape(candidate.get("id", ""))}/evaluate">
<p><label for="evaluate-level">{escape(_copy("label.evaluate_level", locale))}</label> <input id="evaluate-level" type="number" min="1" max="3" name="level" value="1"></p>
<p><button type="submit">{escape(_copy("action.evaluate", locale))}</button></p>
</form>
<hr>
<form method="post" action="/app/ui/candidates/{escape(candidate.get("id", ""))}/approve">
<p><label for="approve-override">{escape(_copy("label.override_reason", locale))}</label> <input id="approve-override" name="override_reason"></p>
<p><label><input type="checkbox" name="force_critical" value="true"> {escape(_copy("label.force_critical_approve", locale))}</label></p>
<p><button type="submit">{escape(_copy("action.approve", locale))}</button></p>
</form>
<hr>
<form method="post" action="/app/ui/candidates/{escape(candidate.get("id", ""))}/reject">
<p><label for="reject-reason">{escape(_copy("label.reject_reason", locale))}</label> <input id="reject-reason" name="reason"></p>
<p><button type="submit">{escape(_copy("action.reject", locale))}</button></p>
</form>
<hr>
<form method="post" action="/app/ui/candidates/{escape(candidate.get("id", ""))}/revise">
<p><label for="revise-content"><strong>{escape(_copy("label.revised_content", locale))}</strong></label></p>
<p><textarea id="revise-content" name="edited_text" rows="8" style="width:100%;">{escape(candidate.get("content", ""))}</textarea></p>
<p><label for="revise-section">{escape(_copy("label.target_section", locale))}</label> <input id="revise-section" name="target_section" value="{escape(proposal.get("section", ""))}"></p>
<p><label for="revise-reason">{escape(_copy("label.change_reason", locale))}</label> <input id="revise-reason" name="change_reason"></p>
<p><button type="submit">{escape(_copy("action.create_revised_candidate", locale))}</button></p>
</form>
"""
    )
    body = f"""
<h1>{escape(_copy("heading.detail", locale))}</h1>
<p><a href="/app/ui/candidates">{escape(_copy("action.back_to_queue", locale))}</a> · <a href="{escape(diff_path)}">{escape(_copy("action.open_diff", locale))}</a></p>
{detail_meta_panel}
{detail_cards}
{guidance}
{content_panel}
{_render_candidate_mapping(locale, _copy("mapping.proposal", locale), proposal)}
{_render_candidate_mapping(locale, _copy("mapping.evaluation", locale), evaluation)}
{actions_panel}
<p class="muted">{escape(_copy("desc.detail_boundary", locale))}</p>
"""
    return _page(_copy("title.detail", locale), body, locale=locale, notice=notice, error=error)


def render_resident_app_candidate_diff(
    candidate_id: str,
    diff: dict[str, Any],
    *,
    locale: str = DEFAULT_BOOTSTRAP_LOCALE,
    notice: str | None = None,
    error: str | None = None,
) -> str:
    diff_summary = diff.get("ui_summary", {})
    body = f"""
<h1>{escape(_copy("heading.diff", locale))}</h1>
<p><a href="/app/ui/candidates/{escape(candidate_id)}">{escape(_copy("action.back_to_detail", locale))}</a></p>
{_render_panel(_copy("label.diff_summary", locale), _render_kv_panel(locale, diff_summary) if diff_summary else f'<p class="muted">{escape(_copy("label.diff_summary_missing", locale))}</p>')}
{_render_panel(_copy("label.diff_payload", locale), _render_json_fallback(diff))}
<p class="muted">{escape(_copy("desc.diff", locale))}</p>
"""
    return _page(_copy("title.diff", locale), body, locale=locale, notice=notice, error=error)


def render_resident_app_daemon_panel(
    payload: dict[str, Any],
    *,
    locale: str = DEFAULT_BOOTSTRAP_LOCALE,
    notice: str | None = None,
    error: str | None = None,
) -> str:
    status = payload.get("status", {})
    readiness = payload.get("readiness", {})
    runtime_init = payload.get("runtime_init", {})
    cleanup_preview = payload.get("cleanup_preview", {})
    repair_preview = payload.get("repair_preview", {})
    packaging_status = payload.get("packaging_status", {})
    service_control_boundary = payload.get("service_control_boundary", {})
    supervision_status = payload.get("supervision_status", {})
    recovery_consent_status = payload.get("recovery_consent_status", {})
    service_targets_status = payload.get("service_targets_status", {})
    launchagent_preview = payload.get("launchagent_preview")
    launchagent_status = payload.get("launchagent_status")
    next_actions = payload.get("next_actions", [])
    action_html = "".join(
        (
                "<li>"
                f'<strong>{escape(action.get("command", ""))}</strong><br>'
                f'<span class="muted">{escape(_translate_display_phrase(action.get("reason", ""), locale))}</span>'
                "</li>"
            )
        for action in next_actions
    ) or f'<li class="muted">{escape(_copy("empty.immediate_daemon_actions", locale))}</li>'
    packaging_panel = _render_panel(
        _copy("label.packaging_status", locale),
        _render_kv_panel(
            locale,
            packaging_status,
            keys=["kind", "packaging_model", "supervision_model", "phase_status"],
        ) if packaging_status else _render_json_fallback(packaging_status),
    )
    service_control_content = (
        _render_kv_panel(
            locale,
            {
                "kind": service_control_boundary.get("kind"),
                "control_plane_status": service_control_boundary.get("control_plane", {}).get("status"),
                "service_plane_status": service_control_boundary.get("service_plane", {}).get("status"),
            },
        )
        + f"<h3>{escape(_copy('label.allowed_commands', locale))}</h3>"
        + _render_string_list(
            [item.get("command", "") for item in service_control_boundary.get("control_plane", {}).get("allowed_commands", [])]
            + [item.get("command", "") for item in service_control_boundary.get("service_plane", {}).get("allowed_commands", [])],
            empty_label=_copy("detail.empty_preview", locale),
        )
        + f"<h3>{escape(_copy('label.deferred_commands', locale))}</h3>"
        + _render_string_list(
            service_control_boundary.get("service_plane", {}).get("deferred_commands", []),
            empty_label=_copy("detail.empty_preview", locale),
        )
    ) if service_control_boundary else _render_json_fallback(service_control_boundary)
    service_control_panel = _render_panel(_copy("label.service_control_boundary", locale), service_control_content)
    supervision_content = (
        _render_kv_panel(
            locale,
            {
                "kind": supervision_status.get("kind"),
                "supervision_mode": supervision_status.get("supervision_mode"),
                "phase_status": supervision_status.get("phase_status"),
                "active_supervision_status": supervision_status.get("active_supervision", {}).get("status"),
            },
        )
        + f"<h3>{escape(_copy('label.allowed_commands', locale))}</h3>"
        + _render_string_list(
            supervision_status.get("active_supervision", {}).get("allowed_actions", []),
            empty_label=_copy("detail.empty_preview", locale),
        )
    ) if supervision_status else _render_json_fallback(supervision_status)
    supervision_panel = _render_panel(_copy("label.supervision_status", locale), supervision_content)
    recommended_flow_items = recovery_consent_status.get("recommended_recovery_flow", [])
    recommended_flow_html = (
        "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in recommended_flow_items) + "</ul>"
        if recommended_flow_items
        else f'<p class="muted">{escape(_copy("detail.empty_preview", locale))}</p>'
    )
    recovery_content = (
        _render_kv_panel(
            locale,
            {
                "kind": recovery_consent_status.get("kind"),
                "consent_model": recovery_consent_status.get("consent_model"),
                "recovery_model": recovery_consent_status.get("recovery_model"),
                "phase_status": recovery_consent_status.get("phase_status"),
            },
        )
        + f"<h3>{escape(_copy('label.recommended_flow', locale))}</h3>"
        + recommended_flow_html
    ) if recovery_consent_status else _render_json_fallback(recovery_consent_status)
    recovery_panel = _render_panel(_copy("label.recovery_consent_status", locale), recovery_content)
    body = f"""
<h1>{escape(_copy("heading.daemon", locale))}</h1>
<p><a href="/app/ui">{escape(_copy("action.back_to_home", locale))}</a></p>
{_render_cards_grid([
    _render_card(_copy("label.daemon_state", locale), _translate_display_token(status.get("state", ""), locale)),
    _render_card(_copy("label.running", locale), _translate_display_token(status.get("is_running_daemon", ""), locale)),
    _render_card(_copy("label.runtime_initialized", locale), _translate_display_token(status.get("runtime_initialized", ""), locale)),
    _render_card(_copy("label.readiness", locale), _translate_display_token(readiness.get("readiness_status", ""), locale)),
])}
{_render_panel(_copy("label.next_actions", locale), f"<ul>{action_html}</ul>")}
{_render_panel(_copy("label.runtime_init_preview", locale), _render_runtime_init_preview(locale, runtime_init) if runtime_init else _render_json_fallback(runtime_init))}
{_render_panel(_copy("label.cleanup_preview", locale), _render_cleanup_preview(locale, cleanup_preview) if cleanup_preview else _render_json_fallback(cleanup_preview))}
{_render_panel(_copy("label.repair_preview", locale), _render_repair_preview(locale, repair_preview) if repair_preview else _render_json_fallback(repair_preview))}
{packaging_panel}
{service_control_panel}
{supervision_panel}
{recovery_panel}
{_render_panel(_copy("label.service_targets", locale), _render_service_targets_status(locale, service_targets_status) if service_targets_status else _render_json_fallback(service_targets_status))}
{_render_panel(_copy("label.launchagent_preview", locale), _render_launchagent_preview(locale, launchagent_preview))}
{_render_panel(_copy("label.launchagent_status", locale), _render_launchagent_status(locale, launchagent_status))}
<p class="muted">{escape(_copy("desc.daemon", locale))}</p>
"""
    return _page(_copy("title.daemon", locale), body, locale=locale, notice=notice, error=error)
