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
    #expect(strings.tone(forToken: "running") == .positive)
    #expect(strings.tone(forToken: "separate_plan_required") == .critical)
    #expect(strings.text(.needsAttention) == "要対応")
    #expect(strings.text(.diagnosticPriority) == "復旧優先度")
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
    #expect(strings.text(.timelineEvent) == "イベント")
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
    #expect(strings.text(.noCandidates) == "候補はまだありません")
    #expect(strings.text(.noCandidatesMatchingFilters) == "現在のフィルタ条件に一致する候補はありません")
    #expect(strings.text(.selectCandidatePrompt) == "候補を選ぶと、詳細・差分・来歴をここに表示します")
    #expect(strings.text(.loadingCandidates) == "候補と詳細を更新しています")
    #expect(strings.text(.sectionNavigator) == "セクション移動")
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
    #expect(strings.text(.back) == "戻る")
    #expect(strings.text(.navigationTrail) == "移動履歴")
    #expect(strings.text(.connectionDiagnostics) == "接続診断")
    #expect(strings.text(.bridgeStatusPanel) == "Bridge 状態")
    #expect(strings.text(.bridgeReady) == "Bridge は利用可能です")
    #expect(strings.text(.bridgeStarting) == "Bridge は起動中です")
    #expect(strings.text(.bridgeNotConnected) == "Bridge に未接続です")
    #expect(strings.text(.debugShell) == "Debug Shell")
    #expect(strings.text(.openToken) == "token を開く")
    #expect(strings.text(.copyHealthCommand) == "health command をコピー")
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
    #expect(strings.evaluateActionMessage(id: "cand-001", level: 2) == "評価完了: cand-001 (L2)")
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
@Test func appModelFindsSelectedCandidateActionRecord() {
    let model = AppModel()
    model.selectedCandidateID = "cand-201"
    model.lastCandidateAction = AppModel.CandidateActionRecord(
        candidateIDs: ["cand-101", "cand-201"],
        title: "完了",
        message: "評価完了: cand-201 (L1)",
        tone: .positive
    )

    #expect(model.selectedCandidateActionRecord?.message == "評価完了: cand-201 (L1)")

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
