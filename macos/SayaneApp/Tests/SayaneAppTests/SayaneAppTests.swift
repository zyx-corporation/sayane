import Foundation
import Testing
@testable import SayaneApp

@Test func appStringsHaveJapaneseTitle() {
    let strings = AppStrings(language: .ja)
    #expect(strings.text(.appTitle) == "紗綾音 Resident App")
}

@Test func appStringsLocalizeSummaryCardLabels() {
    let strings = AppStrings(language: .ja)
    #expect(strings.summaryCardLabel("repository") == "リポジトリ")
    #expect(strings.summaryCardLabel("readiness_status") == "準備状況")
    #expect(strings.fieldLabel("section") == "セクション")
    #expect(strings.statusValueLabel("pending") == "保留")
    #expect(strings.lineageDetailLabel("candidate_id") == "候補ID")
    #expect(strings.tokenLabel("cli_first_local_bridge") == "CLI先行 + Local Bridge")
    #expect(strings.summaryValueLabel(key: "state", value: "running") == "稼働中")
    #expect(strings.booleanValueLabel(true) == "はい")
    #expect(strings.booleanValueLabel(false) == "いいえ")
    #expect(strings.tone(forToken: "running") == .positive)
    #expect(strings.tone(forToken: "separate_plan_required") == .critical)
    #expect(strings.text(.needsAttention) == "要対応")
    #expect(strings.text(.diagnosticPriority) == "復旧優先度")
    #expect(strings.text(.proofDiagnostics) == "Proof診断")
    #expect(strings.text(.proofDiagnosticsSummary) == "identity / readiness / API readiness の proof-oriented 読み取りコマンドです")
    #expect(strings.text(.previousCandidate) == "前の候補")
    #expect(strings.text(.commandDeck) == "操作デッキ")
    #expect(strings.text(.inspectActions) == "確認")
    #expect(strings.text(.searchCandidates) == "候補を検索")
    #expect(strings.text(.allStatuses) == "全ステータス")
    #expect(strings.text(.clearFilters) == "解除")
    #expect(strings.text(.quickFilters) == "クイックフィルタ")
    #expect(strings.text(.sortOrder) == "並び順")
    #expect(strings.text(.sortNewest) == "新しい順")
    #expect(strings.text(.diffSummary) == "差分サマリー")
    #expect(strings.text(.addedItems) == "追加候補")
    #expect(strings.fieldLabel("proposal_section") == "提案セクション")
    #expect(strings.fieldLabel("captured_at") == "取り込み日時")
    #expect(strings.fieldLabel("status") == "状態")
    #expect(strings.text(.recommended) == "推奨")
    #expect(strings.text(.timelineEvent) == "イベント")
    #expect(strings.text(.loadedStatus) == "読み込み状態")
    #expect(strings.text(.currentState) == "現在状態")
    #expect(strings.text(.currentValue) == "現在")
    #expect(strings.text(.mode) == "モード")
    #expect(strings.text(.consent) == "同意")
    #expect(strings.text(.recovery) == "復旧")
    #expect(strings.fieldLabel("label") == "ラベル")
    #expect(strings.fieldLabel("plist_exists") == "plist 存在")
    #expect(strings.tokenLabel("ready") == "準備完了")
    #expect(strings.tokenLabel("review_required") == "レビュー要")
    #expect(strings.homeDaemonActionSummary(for: "curl -s http://127.0.0.1:38741/health") == "現在の Bridge / launchd 状態を先に確認します。")
    #expect(strings.runtimeInitSummary(reviewRequired: true, itemCount: 2) == "レビュー要 (2)")
    #expect(strings.cleanupSummary(removeCount: 1, totalCount: 3) == "削除候補=1, 合計=3")
    #expect(strings.diagnosticMessage("launchagent_loaded") == "launchagent は読み込み済みです。")
    #expect(strings.securityBoundaryNotes().first == "bind host は 127.0.0.1 のまま維持します")
    #expect(strings.previewApplyBoundaryNotes().first == "preview はファイル変更やサービス読み込みを行いません")
    #expect(strings.captureActionMessage(id: "cand-001") == "取り込み完了: cand-001")
    #expect(strings.copiedCommandMessage(context: strings.fieldLabel("stderr")) == "コピーしました: stderr")
    #expect(strings.text(.quickLinks) == "クイックリンク")
    #expect(strings.text(.screenOverview) == "表示中")
    #expect(strings.quickLinkLabel(screen: "candidate_queue") == "候補キューを開く")
    #expect(strings.quickLinkLabel(screen: "daemon_panel") == "デーモンを開く")
    #expect(strings.text(.noCandidates) == "候補はまだありません")
    #expect(strings.text(.noCandidatesMatchingFilters) == "現在のフィルタ条件に一致する候補はありません")
    #expect(strings.text(.selectCandidatePrompt) == "候補を選ぶと、詳細・差分・来歴をここに表示します")
    #expect(strings.text(.loadingCandidates) == "候補と詳細を更新しています")
    #expect(strings.text(.sectionNavigator) == "セクション移動")
    #expect(strings.text(.sectionNavigatorSummary) == "優先度の高いセクションへすぐ移動できます")
    #expect(strings.text(.prioritySections) == "優先セクション")
    #expect(strings.text(.otherSections) == "その他のセクション")
    #expect(strings.text(.expandAll) == "すべて開く")
    #expect(strings.text(.collapseAll) == "すべて閉じる")
    #expect(strings.text(.noNextActions) == "次のアクションはありません")
    #expect(strings.text(.filteredCandidates) == "表示候補")
    #expect(strings.text(.activeFilters) == "有効フィルタ")
    #expect(strings.text(.noActiveFilters) == "フィルタなし")
    #expect(strings.text(.actionReadiness) == "実行可能アクション")
    #expect(strings.text(.shortcutLabel) == "ショートカット")
    #expect(strings.text(.enabled) == "有効")
    #expect(strings.text(.disabled) == "無効")
    #expect(strings.text(.approve) == "承認")
    #expect(strings.text(.back) == "戻る")
    #expect(strings.text(.navigationTrail) == "移動履歴")
    #expect(strings.text(.connectionDiagnostics) == "接続診断")
    #expect(strings.text(.bridgeStatusPanel) == "Bridge 状態")
    #expect(strings.text(.bridgeReady) == "Bridge は利用可能です")
    #expect(strings.text(.bridgeStarting) == "Bridge は起動中です")
    #expect(strings.text(.bridgeNotConnected) == "Bridge に未接続です")
    #expect(strings.text(.debugShell) == "ブラウザ fallback（デバッグ用）")
    #expect(strings.text(.debugShellCompatibilitySummary) == "通常操作ではなく、ブラウザでのデバッグ / fallback / handoff 用の経路です")
    #expect(strings.text(.bootstrapUI) == "デバッグ用 fallback URL")
    #expect(strings.text(.openToken) == "token を開く")
    #expect(strings.text(.copyHealthCommand) == "health command をコピー")
    #expect(strings.text(.copyStartupCommand) == "起動コマンドをコピー")
    #expect(strings.text(.copyDetail) == "詳細をコピー")
    #expect(strings.text(.copyDiff) == "差分をコピー")
    #expect(strings.text(.copyLineage) == "来歴をコピー")
    #expect(strings.text(.copyCurrentState) == "現在状態をコピー")
    #expect(strings.text(.copyRecoveryPreview) == "復旧プレビューをコピー")
    #expect(strings.text(.copyOperatorSummary) == "運用サマリーをコピー")
    #expect(strings.text(.copyPhaseGates) == "Phaseゲートをコピー")
    #expect(strings.text(.copyReadSurfaces) == "参照先をコピー")
    #expect(strings.text(.copySuggestedActions) == "推奨アクションをコピー")
    #expect(strings.text(.exportHandoffNote) == "handoff noteを書き出す")
    #expect(strings.text(.savedFile) == "保存しました")
    #expect(strings.text(.generatedAt) == "生成日時")
    #expect(strings.text(.bridgeContext) == "Bridgeコンテキスト")
    #expect(strings.text(.component) == "コンポーネント")
    #expect(strings.text(.statusDiagnostics) == "状態診断")
    #expect(strings.text(.returnCode) == "リターンコード")
    #expect(strings.text(.bridgeVersion) == "バージョン")
    #expect(strings.text(.sourceUpdatedAt) == "ソース更新時刻")
    #expect(strings.text(.healthEndpoint) == "health エンドポイント")
    #expect(strings.text(.tokenFile) == "トークンファイル")
    #expect(strings.text(.logFile) == "ログファイル")
    #expect(strings.text(.profile) == "プロファイル")
    #expect(strings.text(.tailLogs) == "ログ追跡コマンド")
    #expect(strings.text(.launchctlPrint) == "launchctl print")
    #expect(strings.text(.stdoutTail) == "stdout tail")
    #expect(strings.text(.stderrTail) == "stderr tail")
    #expect(strings.savedFileMessage(path: "/tmp/sample.txt") == "ファイル保存: /tmp/sample.txt")
    #expect(strings.tone(forCommand: "sayane app daemon-repair-preview --json") == .critical)
    #expect(strings.tone(forCommand: "launchctl print gui/501/example") == .positive)
    #expect(strings.commandPriorityTitle(for: "sayane app daemon-service-targets-status --json") == "確認ポイント")
    #expect(strings.text(.actionCompleted) == "完了")
    #expect(strings.text(.actionFailed) == "失敗")
    #expect(strings.text(.candidateResult) == "候補結果")
    #expect(strings.text(.resultForCurrentCandidate) == "この候補の直近結果")
    #expect(strings.text(.shortcutGuide) == "ショートカット一覧")
    #expect(strings.text(.startHere) == "まずここから")
    #expect(strings.text(.noPriorityActions) == "今すぐ着手すべき項目はありません")
    #expect(strings.text(.reviewNextCandidate) == "次の候補を確認")
    #expect(strings.text(.reviewDaemonAction) == "デーモンの次アクションを確認")
    #expect(strings.text(.checkLaunchAgentStatus) == "LaunchAgent 状態を確認")
    #expect(strings.text(.openRunbook) == "Runbook を開く")
    #expect(strings.text(.launchAgentFocus) == "LaunchAgent Focus")
    #expect(strings.text(.launchAgentFocusSummary) == "現在状態、復旧プレビュー、次コマンドを先にまとめて見ます")
    #expect(strings.text(.currentStateDetails) == "現在状態の詳細")
    #expect(strings.text(.currentStateDetailsSummary) == "LaunchAgent Focusで見た要約の根拠をここで確認します")
    #expect(strings.text(.recoveryPreviewDetails) == "復旧プレビューの詳細")
    #expect(strings.text(.recoveryPreviewDetailsSummary) == "Focusで見た復旧要約の内訳と注意点をここで確認します")
    #expect(strings.text(.nextEpicWorkspace) == "次のEpicワークスペース")
    #expect(strings.text(.remainingWorkstreams) == "残りの判断面")
    #expect(strings.text(.remainingWorkstreamsSummary) == "上の優先導線で触れていない判断面だけをここに残します")
    #expect(strings.text(.priorityPathCoversCurrentWorkspace) == "現在の優先導線が主要な判断面をすでにカバーしています")
    #expect(strings.text(.operatorSummaryRail) == "運用サマリーレール")
    #expect(strings.text(.operatorSummaryRailSummary) == "現在のゲート、次コマンド、次の確認先を最初にひとまとめで見ます")
    #expect(strings.text(.nextEpicWorkspaceSummary) == "次の判断面とブロッカーをまとめて見ます")
    #expect(strings.text(.operatorWorkspaceCompactSummary) == "重要な判断面を優先順とブロッカー付きで見ます")
    #expect(strings.text(.currentGate) == "現在のゲート")
    #expect(strings.text(.nextReadSurface) == "次の確認先")
    #expect(strings.text(.phaseClosureGates) == "Phase完了ゲート")
    #expect(strings.text(.phaseClosureGatesSummary) == "未完了ゲートと確認先を対応づけて示します")
    #expect(strings.text(.openSection) == "セクションを開く")
    #expect(strings.text(.nextCommand) == "次のコマンド")
    #expect(strings.text(.additionalBlockers) == "追加ブロッカー")
    #expect(strings.residentValueLabel("knowledge.preferences") == "知識 / 嗜好")
    #expect(strings.copiedCommandMessage(context: "Phase完了ゲート") == "コピーしました: Phase完了ゲート")
    #expect(strings.text(.evidenceDrilldown) == "根拠ドリルダウン")
    #expect(strings.text(.evidenceDrilldownSummary) == "関連する read surface を見比べて確認先を絞ります")
    #expect(strings.text(.decisionAssist) == "判断支援")
    #expect(strings.text(.decisionAssistSummary) == "次の一手を要約とコマンドで先に示します")
    #expect(strings.text(.inspectActionsSummary) == "現在の launchd 状態と Bridge health を非破壊で確認します")
    #expect(strings.text(.recoverActionsSummary) == "cleanup / repair / bootout の順で古い状態を解消します")
    #expect(strings.text(.startActionsSummary) == "復旧確認後に bootstrap / kickstart で起動します")
    #expect(strings.text(.logActionsSummary) == "ログの場所を確認してから tail で追跡します")
    #expect(strings.text(.statusSectionSummary) == "各運用面の状態・注目点・代表コマンドを短く見ます")
    #expect(strings.moreItemsMessage(3) == "ほか 3 件")
    #expect(strings.tone(forToken: "candidate_approved") == .neutral)
    #expect(strings.lineageDetailLabel("source_candidate_id") == "元候補ID")
    #expect(strings.text(.serviceControlAssistSummary) == "まず service control boundary を確認して、許可された local control を見極めます")
    #expect(strings.text(.launchAgentAssistRuntimeInit) == "runtime init preview を先に確認します")
    #expect(strings.summaryCardLabel("packaging_model_decision") == "パッケージング判断")
    #expect(strings.summaryCardLabel("service_integration_line") == "サービス統合")
    #expect(strings.summaryCardLabel("supervision_ux_line") == "監視UX判断")
    #expect(strings.summaryCardLabel("recovery_and_consent_line") == "復旧と同意")
    #expect(strings.summaryCardLabel("service_control_boundary_definition") == "サービス制御境界")
    #expect(strings.summaryCardLabel("supported_packaging_model_finalized") == "サポートするパッケージング判断")
    #expect(strings.tokenLabel("baseline_contract_implemented") == "契約ベースライン実装済み")
    #expect(strings.tokenLabel("blocked") == "ブロック中")
    #expect(strings.operatorPanelPriority("packaging_status") < strings.operatorPanelPriority("service_targets"))
    #expect(strings.operatorPanelPriority("service_targets") < strings.operatorPanelPriority("operator_phase_status"))
    #expect(strings.highlightPriority("separate_plan_required") < strings.highlightPriority("review_required"))
    #expect(strings.highlightPriority("review_required") < strings.highlightPriority("available"))
    #expect(strings.residentValueLabel("knowledge.concepts") == "知識 / 概念")
    #expect(strings.residentValueLabel("clipboard") == "クリップボード")
    #expect(strings.residentValueLabel("add") == "追加")
    #expect(strings.residentValueLabel("Preserved") == "保存された要素")
    #expect(strings.evaluationLevelLabel(1) == "クイック確認")
    #expect(strings.evaluationLevelLabel(2) == "ローカルAI確認")
    #expect(strings.evaluationLevelLabel(3, detailed: true) == "外部AI確認（ローカルAI確認とクイック確認を含む）")
    #expect(strings.evaluateActionMessage(id: "cand-001", level: 2) == "評価完了: cand-001（ローカルAI確認）")
    #expect(strings.approveActionMessage(id: "cand-001") == "承認完了: cand-001")
    #expect(strings.rejectActionMessage(id: "cand-001") == "却下完了: cand-001")
    #expect(strings.reviseActionMessage(id: "cand-002", originalID: "cand-001") == "修正版を作成: cand-001 → cand-002")
}

@MainActor
@Test func appModelSelectsPreviousAndNextCandidate() {
    let model = AppModel()
    model.queueState = CandidateQueueScreenState(
        kind: "resident_app_candidate_queue_screen_state",
        reviewableCount: 2,
        statusCounts: [:],
        topSections: [],
        items: [
            CandidateItem(id: "cand-001", status: "pending", section: nil, content: nil, displaySummary: nil, proposalSection: nil, capturedAt: nil),
            CandidateItem(id: "cand-002", status: "evaluated", section: nil, content: nil, displaySummary: nil, proposalSection: nil, capturedAt: nil),
            CandidateItem(id: "cand-003", status: "approved", section: nil, content: nil, displaySummary: nil, proposalSection: nil, capturedAt: nil),
        ]
    )
    model.selectedCandidateID = "cand-002"

    #expect(model.hasPreviousCandidate)
    #expect(model.hasNextCandidate)

    model.selectPreviousCandidate()
    #expect(model.selectedCandidateID == "cand-001")

    model.selectNextCandidate()
    #expect(model.selectedCandidateID == "cand-002")
}

@MainActor
@Test func appModelBuildsBridgeStatusSummary() {
    let model = AppModel()
    #expect(model.bridgeStatusHeadline == "Bridge に未接続です")
    #expect(model.bridgeSuggestedActionText == "Bridge を起動")

    model.health = HealthResponse(status: "starting", version: "1.0.0", sourceUpdatedAt: nil, component: nil)
    #expect(model.bridgeStatusHeadline == "Bridge は起動中です")
    #expect(model.bridgeSuggestedActionText == "再試行")

    model.health = HealthResponse(status: "ok", version: "1.0.1", sourceUpdatedAt: "2026-06-23T09:00:00Z", component: nil)
    #expect(model.bridgeStatusHeadline == "Bridge は利用可能です")
    #expect(model.bridgeStatusDetail.contains("1.0.1"))
    #expect(model.bridgeSuggestedActionText == "更新")
}

@MainActor
@Test func appModelExposesStartupCommandFromDaemonState() throws {
    let model = AppModel()
    let daemonData = Data(#"""
    {
      "kind": "resident_app_daemon_panel_screen_state",
      "summary_cards": [],
      "operator_panels": [],
      "service_target_summary": {"current_platform": null, "recommended_target": null, "targets": []},
      "launchagent_summary": {"preview_available": false, "status_available": false, "plist_path": null, "loaded_status": null, "launchctl_commands": {}},
      "operator_phase_summary": {"phase": null, "phase_status": null, "phase_readiness": "review_required", "blocking_reasons": [], "checklist": []},
      "operator_phase_details": {
        "current_supported_operator_path": {"startup_command_text": "sayane resident-app bridge", "bootstrap_ui": "http://127.0.0.1:38741/app/ui", "local_only": true, "notes": []},
        "workstreams": [],
        "recommended_implementation_order": [],
        "read_surfaces": [],
        "exit_criteria": [],
        "not_in_scope": []
      },
      "next_actions": [],
      "runtime_init": {},
      "cleanup_preview": {},
      "repair_preview": {}
    }
    """#.utf8)
    model.daemonState = try JSONDecoder().decode(DaemonPanelScreenState.self, from: daemonData)

    #expect(model.startupCommandText == "sayane resident-app bridge")
    #expect(model.currentGateText == nil)
    #expect(model.nextDaemonCommandText == nil)
    #expect(model.nextReadSurfaceText == nil)
}

@MainActor
@Test func appModelExposesCurrentGateAndNextDaemonAction() throws {
    let model = AppModel()
    let daemonData = Data(#"""
    {
      "kind": "resident_app_daemon_panel_screen_state",
      "summary_cards": [],
      "operator_panels": [],
      "service_target_summary": {"current_platform": null, "recommended_target": null, "targets": []},
      "launchagent_summary": {"preview_available": false, "status_available": false, "plist_path": null, "loaded_status": null, "launchctl_commands": {}},
      "operator_phase_summary": {"phase": "current_supported_line", "phase_status": "in_progress", "phase_readiness": "review_required", "blocking_reasons": ["separate_plan_required"], "checklist": []},
      "operator_phase_details": {
        "current_supported_operator_path": {"startup_command_text": "sayane resident-app bridge", "bootstrap_ui": null, "local_only": true, "notes": []},
        "workstreams": [],
        "recommended_implementation_order": [],
        "read_surfaces": [],
        "exit_criteria": [],
        "not_in_scope": []
      },
      "next_actions": [
        {"command": "sayane app daemon-operator-phase-status --json", "reason": "Confirm phase closure blockers."}
      ],
      "runtime_init": {},
      "cleanup_preview": {},
      "repair_preview": {}
    }
    """#.utf8)
    model.daemonState = try JSONDecoder().decode(DaemonPanelScreenState.self, from: daemonData)

    #expect(model.currentGateText == "別計画が必要")
    #expect(model.nextDaemonCommandText == "sayane app daemon-operator-phase-status --json")
    #expect(model.nextDaemonReasonText == "Confirm phase closure blockers.")
    #expect(model.nextReadSurfaceText == nil)
}

@MainActor
@Test func appModelExposesNextReadSurface() throws {
    let model = AppModel()
    let daemonData = Data(#"""
    {
      "kind": "resident_app_daemon_panel_screen_state",
      "summary_cards": [],
      "operator_panels": [],
      "service_target_summary": {"current_platform": null, "recommended_target": null, "targets": []},
      "launchagent_summary": {"preview_available": false, "status_available": false, "plist_path": null, "loaded_status": null, "launchctl_commands": {}},
      "operator_phase_summary": {"phase": "current_supported_line", "phase_status": "in_progress", "phase_readiness": "review_required", "blocking_reasons": [], "checklist": []},
      "operator_phase_details": {
        "current_supported_operator_path": {"startup_command_text": "sayane resident-app bridge", "bootstrap_ui": null, "local_only": true, "notes": []},
        "workstreams": [],
        "recommended_implementation_order": [],
        "read_surfaces": ["sayane app daemon-service-targets-status --json"],
        "exit_criteria": [],
        "not_in_scope": []
      },
      "next_actions": [],
      "runtime_init": {},
      "cleanup_preview": {},
      "repair_preview": {}
    }
    """#.utf8)
    model.daemonState = try JSONDecoder().decode(DaemonPanelScreenState.self, from: daemonData)

    #expect(model.nextReadSurfaceText == "sayane app daemon-service-targets-status --json")
}

@MainActor
@Test func appModelFindsSelectedCandidateActionRecord() {
    let model = AppModel()
    model.selectedCandidateID = "cand-201"
    model.lastCandidateAction = AppModel.CandidateActionRecord(
        candidateIDs: ["cand-101", "cand-201"],
        title: "完了",
        message: "評価完了: cand-201（クイック確認）",
        tone: .positive
    )

    #expect(model.selectedCandidateActionRecord?.message == "評価完了: cand-201（クイック確認）")

    model.selectedCandidateID = "cand-999"
    #expect(model.selectedCandidateActionRecord == nil)
}

@Test func bridgeConfigurationBuildsBootstrapURL() {
    let config = BridgeConfiguration()
    let url = config.bootstrapURL(token: "abc")
    #expect(url.absoluteString.contains("bootstrap_token=abc"))
    #expect(config.healthURL.absoluteString == "http://127.0.0.1:38741/health")
    #expect(config.debugShellURL.absoluteString == "http://127.0.0.1:38741/app/ui")
}

@MainActor
@Test func appModelOpensQuickLinks() {
    let model = AppModel()
    model.queueState = CandidateQueueScreenState(
        kind: "resident_app_candidate_queue_screen_state",
        reviewableCount: 1,
        statusCounts: [:],
        topSections: [],
        items: [
            CandidateItem(id: "cand-101", status: "pending", section: nil, content: nil, displaySummary: nil, proposalSection: nil, capturedAt: nil),
        ]
    )

    model.openQuickLink(QuickLink(screen: "candidate_queue", path: "/app/candidates"))
    #expect(model.selectedScreen == .queue)
    #expect(model.selectedCandidateID == "cand-101")

    model.openQuickLink(QuickLink(screen: "daemon_panel", path: "/app/daemon-overview"))
    #expect(model.selectedScreen == .daemon)
}

@MainActor
@Test func appModelBuildsDaemonClipboardSummaries() throws {
    let model = AppModel()
    model.health = HealthResponse(status: "ok", version: "1.0.12", sourceUpdatedAt: "2026-06-24T10:00:00Z", component: "resident-app-bridge")
    let json = """
    {
      "kind": "resident_app_daemon_panel_screen_state",
      "summary_cards": [],
      "operator_panels": [],
      "service_target_summary": {
        "current_platform": "macos_launchagent",
        "recommended_target": "macos_launchagent",
        "targets": []
      },
      "launchagent_summary": {
        "preview_available": true,
        "status_available": true,
        "plist_path": "/tmp/example.plist",
        "loaded_status": "loaded",
        "launchctl_commands": {}
      },
      "operator_phase_summary": {
        "phase": "current_supported_line",
        "phase_status": "in_progress",
        "phase_readiness": "review_required",
        "blocking_reasons": ["separate_plan_required"],
        "checklist": []
      },
      "operator_phase_details": {
        "current_supported_operator_path": {
          "startup_command_text": "sayane resident-app bridge",
          "bootstrap_ui": "http://127.0.0.1:38741/app/ui",
          "local_only": true,
          "notes": []
        },
        "workstreams": [],
        "recommended_implementation_order": ["packaging_model_decision", "service_integration_line"],
        "read_surfaces": [
          "sayane app daemon-operator-phase-status --json",
          "sayane app daemon-service-targets-status --json"
        ],
        "exit_criteria": [],
        "not_in_scope": []
      },
      "next_actions": [
        {
          "command": "sayane app daemon-operator-phase-status --json",
          "reason": "Confirm phase closure blockers."
        }
      ],
      "runtime_init": {},
      "cleanup_preview": {},
      "repair_preview": {},
      "launchagent_preview": {
        "stdout_path": "/tmp/sayane/stdout.log",
        "stderr_path": "/tmp/sayane/stderr.log"
      },
      "launchagent_status": {
        "print_command": "launchctl print gui/501/io.sayane.bridge"
      },
      "operator_phase_status": {
        "phase_closure_checklist": [
          {
            "item": "Packaging decision documented",
            "status": "review_required",
            "blocking_reasons": ["separate_plan_required", "blocked"]
          }
        ]
      }
    }
    """
    model.daemonState = try JSONDecoder().decode(DaemonPanelScreenState.self, from: Data(json.utf8))

    let summary = try #require(model.daemonOperatorSummaryClipboardText())
    #expect(summary.contains("運用サマリーレール"))
    #expect(summary.contains("準備状況: レビュー要"))
    #expect(summary.contains("現在のゲート: 別計画が必要"))
    #expect(summary.contains("sayane app daemon-operator-phase-status --json"))

    let gates = try #require(model.daemonPhaseGatesClipboardText())
    #expect(gates.contains("Packaging decision documented"))
    #expect(gates.contains("未解決ブロッカー: 別計画が必要"))

    let readSurfaces = try #require(model.daemonReadSurfacesClipboardText())
    #expect(readSurfaces.contains("1. sayane app daemon-operator-phase-status --json"))

    let suggestedActions = try #require(model.daemonSuggestedActionsClipboardText())
    #expect(suggestedActions.contains("推奨アクション"))
    #expect(suggestedActions.contains("Confirm phase closure blockers."))

    let handoff = try #require(model.daemonHandoffExportText())
    #expect(handoff.contains("Handoff Snapshot"))
    #expect(handoff.contains("Bridgeコンテキスト:"))
    #expect(handoff.contains("生成日時: "))
    #expect(handoff.contains("プロファイル: default"))
    #expect(handoff.contains("Bridge URL: http://127.0.0.1:38741"))
    #expect(handoff.contains("health エンドポイント: http://127.0.0.1:38741/health"))
    #expect(handoff.contains("ブラウザ fallback（デバッグ用）: http://127.0.0.1:38741/app/ui"))
    #expect(handoff.contains("トークンファイル: "))
    #expect(handoff.contains(".sayane/bridge.token"))
    #expect(handoff.contains("ログファイル: "))
    #expect(handoff.contains(".sayane/run-app-local.log"))
    #expect(handoff.contains("Bridge 状態: Bridge は利用可能です"))
    #expect(handoff.contains("コンポーネント: resident-app-bridge"))
    #expect(handoff.contains("バージョン: 1.0.12"))
    #expect(handoff.contains("ソース更新時刻: 2026-06-24T10:00:00Z"))
    #expect(handoff.contains("状態診断:"))
    #expect(handoff.contains("• 次のコマンド: sayane app daemon-operator-phase-status --json"))
    #expect(handoff.contains("• 理由: Confirm phase closure blockers."))
    #expect(handoff.contains("• launchctl print: launchctl print gui/501/io.sayane.bridge"))
    #expect(handoff.contains("ログ追跡コマンド:"))
    #expect(handoff.contains("• stdout tail: tail -f /tmp/sayane/stdout.log"))
    #expect(handoff.contains("• stderr tail: tail -f /tmp/sayane/stderr.log"))
    #expect(handoff.contains("事前確認:"))
    #expect(handoff.contains("• sayane app daemon-preflight --json"))
    #expect(handoff.contains("Proof診断:"))
    #expect(handoff.contains("• sayane app daemon-proof-diagnostics --operation-class bridge_health --json"))
    #expect(handoff.contains("運用サマリーレール:"))
    #expect(handoff.contains("Phase完了ゲート:"))
    #expect(handoff.contains("推奨アクション:"))
    #expect(handoff.contains("参照サーフェス:"))
    #expect(handoff.contains("現在状態:"))
    #expect(handoff.contains("復旧プレビュー:"))
    let operatorSummaryIndex = try #require(handoff.range(of: "運用サマリーレール:")?.lowerBound)
    let bridgeContextIndex = try #require(handoff.range(of: "Bridgeコンテキスト:")?.lowerBound)
    let suggestedActionIndex = try #require(handoff.range(of: "推奨アクション:")?.lowerBound)
    let phaseGatesIndex = try #require(handoff.range(of: "Phase完了ゲート:")?.lowerBound)
    let readSurfacesIndex = try #require(handoff.range(of: "参照サーフェス:")?.lowerBound)
    let currentStateIndex = try #require(handoff.range(of: "現在状態:")?.lowerBound)
    #expect(bridgeContextIndex < operatorSummaryIndex)
    #expect(operatorSummaryIndex < suggestedActionIndex)
    #expect(suggestedActionIndex < phaseGatesIndex)
    #expect(phaseGatesIndex < readSurfacesIndex)
    #expect(readSurfacesIndex < currentStateIndex)
    #expect(model.daemonHandoffExportFilename().hasPrefix("sayane-daemon-handoff-"))
    #expect(model.daemonHandoffExportFilename().hasSuffix(".txt"))
}

@MainActor
@Test func appModelBackRestoresPreviousNavigationState() {
    let model = AppModel()
    model.queueState = CandidateQueueScreenState(
        kind: "resident_app_candidate_queue_screen_state",
        reviewableCount: 2,
        statusCounts: [:],
        topSections: [],
        items: [
            CandidateItem(id: "cand-201", status: "pending", section: nil, content: nil, displaySummary: nil, proposalSection: nil, capturedAt: nil),
            CandidateItem(id: "cand-202", status: "approved", section: nil, content: nil, displaySummary: nil, proposalSection: nil, capturedAt: nil),
        ]
    )

    #expect(model.navigationTrailText == "ホーム")
    #expect(model.canGoBack == false)

    model.openCandidate("cand-201")
    #expect(model.selectedScreen == .queue)
    #expect(model.selectedCandidateID == "cand-201")
    #expect(model.canGoBack)
    #expect(model.navigationTrailText == "ホーム → 候補キュー → cand-201")

    model.choose(screen: .daemon)
    #expect(model.selectedScreen == .daemon)
    #expect(model.navigationTrailText == "ホーム → デーモン")

    model.goBack()
    #expect(model.selectedScreen == .queue)
    #expect(model.selectedCandidateID == "cand-201")

    model.goBack()
    #expect(model.selectedScreen == .home)
    #expect(model.canGoBack == false)
}

@MainActor
@Test func appModelBuildsSidebarMetadataPerScreen() throws {
    let model = AppModel()
    model.homeState = HomeScreenState(
        kind: "resident_app_home_screen_state",
        summaryCards: [],
        topReviewItems: [
            TopReviewItem(candidateId: "cand-home-1", status: "pending", proposalSection: nil, displaySummary: nil, requiresReview: true),
        ],
        topDaemonActions: [],
        quickLinks: []
    )
    model.queueState = CandidateQueueScreenState(
        kind: "resident_app_candidate_queue_screen_state",
        reviewableCount: 3,
        statusCounts: [:],
        topSections: [],
        items: []
    )
    let daemonData = Data(#"""
    {
      "kind": "resident_app_daemon_panel_screen_state",
      "summary_cards": [],
      "operator_panels": [],
      "service_target_summary": {"current_platform": null, "recommended_target": null, "targets": []},
      "launchagent_summary": {"preview_available": false, "status_available": false, "plist_path": null, "loaded_status": null, "launchctl_commands": {}},
      "operator_phase_summary": {"phase": null, "phase_status": null, "phase_readiness": "review_required", "blocking_reasons": [], "checklist": []},
      "operator_phase_details": {
        "current_supported_operator_path": {"startup_command_text": null, "bootstrap_ui": null, "local_only": null, "notes": []},
        "workstreams": [],
        "recommended_implementation_order": [],
        "read_surfaces": [],
        "exit_criteria": [],
        "not_in_scope": []
      },
      "next_actions": [],
      "runtime_init": {},
      "cleanup_preview": {},
      "repair_preview": {}
    }
    """#.utf8)
    model.daemonState = try JSONDecoder().decode(DaemonPanelScreenState.self, from: daemonData)

    let home = model.sidebarMetadata(for: .home)
    #expect(home.title == "ホーム")
    #expect(home.summary == "レビュー候補: 1")
    #expect(home.badgeText == "1")
    #expect(home.badgeTone == .positive)

    let queue = model.sidebarMetadata(for: .queue)
    #expect(queue.title == "候補キュー")
    #expect(queue.summary == "レビュー対象: 3")
    #expect(queue.badgeText == "3")
    #expect(queue.badgeTone == .caution)

    let daemon = model.sidebarMetadata(for: .daemon)
    #expect(daemon.title == "デーモン")
    #expect(daemon.summary == "運用フェーズ: レビュー要")
    #expect(daemon.badgeText == "レビュー要")
    #expect(daemon.badgeTone == .neutral)
}

@MainActor
@Test func appModelBuildsCandidateClipboardTexts() {
    let model = AppModel()
    model.selectedCandidateID = "cand-001"
    model.detailState = CandidateDetailScreenState(
        kind: "resident_app_candidate_detail_screen_state",
        uiSummary: CandidateUISummary(
            status: "pending",
            section: "knowledge.concepts",
            operation: "add",
            sourceType: "clipboard",
            evaluationLevel: 2,
            rdeClass: "recommended",
            canApprove: true
        ),
        allowedActions: CandidateAllowedActions(
            evaluate: true,
            approve: true,
            reject: true,
            revise: true,
            showDiff: true
        ),
        proposal: [:],
        evaluation: [:],
        content: "detail body",
        diffAvailable: true
    )
    model.diffState = CandidateDiffPayload(
        reviewSurface: "resident_app_bridge",
        section: "knowledge.concepts",
        recommendedSection: "knowledge.preferences",
        profileUpdateRecommended: true,
        hasDuplicates: false,
        add: ["add one"],
        remove: ["remove one"],
        alreadyPresent: ["keep one"],
        note: "note",
        uiSummary: nil,
        listDiff: nil
    )
    model.lineageState = try? JSONDecoder().decode(
        CandidateLineagePayload.self,
        from: Data(#"""
        {
          "candidate_id": "cand-001",
          "lineage_entries": [
            {
              "summary": "summary",
              "event": "approved",
              "status": "approved"
            }
          ]
        }
        """#.utf8)
    )

    #expect(model.candidateDetailClipboardText()?.contains("detail body") == true)
    #expect(model.candidateDiffClipboardText()?.contains("add one") == true)
    #expect(model.candidateLineageClipboardText()?.contains("summary") == true)
}
