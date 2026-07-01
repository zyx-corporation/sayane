import Foundation
import Testing
@testable import SayaneApp

@Test func appStringsHaveJapaneseTitle() {
    let strings = AppStrings(language: .ja)
    #expect(strings.text(.appTitle) == "紗綾音")
}

@Test func appStringsLocalizeSummaryCardLabels() {
    let strings = AppStrings(language: .ja)
    #expect(strings.summaryCardLabel("repository") == "リポジトリ")
    #expect(strings.summaryCardLabel("readiness_status") == "準備状況")
    #expect(strings.summaryCardLabel("vault_status") == "Vault状態")
    #expect(strings.summaryCardLabel("vault_backend") == "Vault バックエンド")
    #expect(strings.summaryCardLabel("vault_assurance") == "鍵保護")
    #expect(strings.summaryCardLabel("vault_session_count") == "有効セッション数")
    #expect(strings.fieldLabel("section") == "セクション")
    #expect(strings.fieldLabel("backend") == "バックエンド")
    #expect(strings.statusValueLabel("pending") == "保留")
    #expect(strings.lineageDetailLabel("candidate_id") == "候補ID")
    #expect(strings.tokenLabel("cli_first_local_bridge") == "CLI先行 + ローカルバックエンド")
    #expect(strings.tokenLabel("sqlite_test_local_vault") == "SQLite テスト用 Local Vault")
    #expect(strings.tokenLabel("sqlite_development_local_vault") == "SQLite 開発用 Local Vault")
    #expect(strings.tokenLabel("sqlite_macos_keychain_vault") == "SQLite macOS keychain Vault")
    #expect(strings.tokenLabel("os_backed") == "OS保護")
    #expect(strings.tokenLabel("passphrase") == "パスフレーズ")
    #expect(strings.tokenLabel("test_only") == "テスト限定")
    #expect(strings.tokenLabel("deep_private") == "厳重秘匿")
    #expect(strings.tokenLabel("sensitive") == "要保護")
    #expect(strings.tokenLabel("normal") == "通常")
    #expect(strings.tokenLabel("unavailable") == "未利用")
    #expect(strings.tokenLabel("vault_unavailable") == "Vault未接続")
    #expect(strings.summaryValueLabel(key: "state", value: "running") == "稼働中")
    #expect(strings.booleanValueLabel(true) == "はい")
    #expect(strings.booleanValueLabel(false) == "いいえ")
    #expect(strings.tone(forToken: "running") == .positive)
    #expect(strings.tone(forToken: "os_backed") == .positive)
    #expect(strings.tone(forToken: "passphrase") == .caution)
    #expect(strings.tone(forToken: "vault_unavailable") == .critical)
    #expect(strings.tone(forToken: "separate_plan_required") == .critical)
    #expect(strings.text(.localVault) == "Local Vault")
    #expect(strings.text(.vaultPath) == "Vaultパス")
    #expect(strings.text(.vaultSessions) == "アンロックセッション")
    #expect(strings.text(.activeSessions) == "有効セッション")
    #expect(strings.text(.sessionPurpose) == "利用目的")
    #expect(strings.text(.expiresAt) == "有効期限")
    #expect(strings.text(.idleExpiresAt) == "アイドル期限")
    #expect(strings.text(.unlockNormal) == "通常を開く")
    #expect(strings.text(.unlockSensitive) == "要保護を開く")
    #expect(strings.text(.unlockDeepPrivate) == "厳重秘匿を開く")
    #expect(strings.text(.lockAll) == "すべてロック")
    #expect(strings.text(.unlockPolicies) == "アンロックポリシー")
    #expect(strings.text(.recommendedSetup) == "推奨セットアップ")
    #expect(strings.text(.supported) == "対応")
    #expect(strings.text(.notSupported) == "未対応")
    #expect(strings.text(.vaultUnavailable) == "Local Vault はまだ通常ランタイムに接続されていません")
    #expect(strings.text(.backend) == "バックエンド")
    #expect(strings.text(.needsAttention) == "要対応")
    #expect(strings.text(.diagnosticPriority) == "復旧優先度")
    #expect(strings.text(.proofDiagnostics) == "根拠診断")
    #expect(strings.text(.proofDiagnosticsSummary) == "identity / readiness / API readiness を根拠付きで確認する読み取りコマンドです")
    #expect(strings.text(.previousCandidate) == "前の候補")
    #expect(strings.text(.commandDeck) == "操作デッキ")
    #expect(strings.text(.inspectActions) == "確認")
    #expect(strings.text(.searchCandidates) == "候補を絞り込む")
    #expect(strings.text(.allStatuses) == "全ステータス")
    #expect(strings.text(.clearFilters) == "解除")
    #expect(strings.text(.quickFilters) == "絞り込み候補")
    #expect(strings.text(.sortOrder) == "並び順")
    #expect(strings.text(.sortNewest) == "新しい順")
    #expect(strings.text(.diffSummary) == "差分の要約")
    #expect(strings.text(.addedItems) == "追加候補")
    #expect(strings.fieldLabel("proposal_section") == "提案セクション")
    #expect(strings.fieldLabel("captured_at") == "取り込み日時")
    #expect(strings.fieldLabel("status") == "状態")
    #expect(strings.text(.recommended) == "推奨")
    #expect(strings.text(.timelineEvent) == "イベント")
    #expect(strings.text(.loadedStatus) == "読み込み状態")
    #expect(strings.text(.currentState) == "現在状態")
    #expect(strings.text(.currentValue) == "現在")
    #expect(strings.text(.primaryOperatorUI) == "主要オペレーターUI")
    #expect(strings.text(.recommendedLauncher) == "推奨ランチャー")
    #expect(strings.text(.operatorSurfaceNotes) == "運用サーフェス補足")
    #expect(strings.text(.openLauncher) == "ランチャーを開く")
    #expect(strings.text(.mode) == "モード")
    #expect(strings.text(.scope) == "対象範囲")
    #expect(strings.text(.consent) == "同意")
    #expect(strings.text(.recovery) == "復旧")
    #expect(strings.text(.allowedWrites) == "許可された書き込み")
    #expect(strings.text(.allowedControlExposure) == "許可された制御公開")
    #expect(strings.text(.platformTargets) == "対象サービス")
    #expect(strings.fieldLabel("label") == "ラベル")
    #expect(strings.fieldLabel("plist_exists") == "plist 存在")
    #expect(strings.tokenLabel("ready") == "準備完了")
    #expect(strings.tokenLabel("review_required") == "レビュー要")
    #expect(strings.homeDaemonActionSummary(for: "curl -s http://127.0.0.1:38741/health") == "現在のバックエンド / launchd 状態を先に確認します。")
    #expect(strings.runtimeInitSummary(reviewRequired: true, itemCount: 2) == "レビュー要 (2)")
    #expect(strings.cleanupSummary(removeCount: 1, totalCount: 3) == "削除候補=1, 合計=3")
    #expect(strings.diagnosticMessage("launchagent_loaded") == "LaunchAgent は読み込み済みです。")
    #expect(strings.securityBoundaryNotes().first == "bind host は 127.0.0.1 のまま維持します")
    #expect(strings.previewApplyBoundaryNotes().first == "preview ではファイル変更やサービス読み込みを行いません")
    #expect(strings.captureActionMessage(id: "cand-001") == "取り込み完了: cand-001")
    #expect(strings.vaultSessionOpenedMessage(level: "sensitive") == "アンロックセッションを開始: 要保護")
    #expect(strings.vaultSessionsLockedMessage() == "アンロックセッションをロックしました")
    #expect(strings.copiedCommandMessage(context: strings.fieldLabel("stderr")) == "コピーしました: stderr")
    #expect(strings.text(.quickLinks) == "クイックリンク")
    #expect(strings.text(.screenOverview) == "表示中")
    #expect(strings.quickLinkLabel(screen: "candidate_queue") == "候補キューを開く")
    #expect(strings.quickLinkLabel(screen: "daemon_panel") == "バックエンド状態を開く")
    #expect(strings.text(.noCandidates) == "候補はまだありません")
    #expect(strings.text(.noCandidatesMatchingFilters) == "条件に一致する候補はありません")
    #expect(strings.text(.selectCandidatePrompt) == "候補を選ぶと、詳細・差分・来歴を表示します")
    #expect(strings.text(.loadingCandidates) == "候補と詳細を更新中です")
    #expect(strings.text(.sectionNavigator) == "セクション移動")
    #expect(strings.text(.sectionNavigatorSummary) == "優先セクションへすぐ移動できます")
    #expect(strings.text(.prioritySections) == "優先セクション")
    #expect(strings.text(.otherSections) == "その他のセクション")
    #expect(strings.text(.expandAll) == "すべて開く")
    #expect(strings.text(.collapseAll) == "すべて閉じる")
    #expect(strings.text(.noNextActions) == "次のアクションはありません")
    #expect(strings.text(.filteredCandidates) == "表示中の候補")
    #expect(strings.text(.activeFilters) == "有効フィルタ")
    #expect(strings.text(.noActiveFilters) == "フィルタなし")
    #expect(strings.text(.actionReadiness) == "実行できるアクション")
    #expect(strings.text(.shortcutLabel) == "ショートカット")
    #expect(strings.text(.enabled) == "有効")
    #expect(strings.text(.disabled) == "無効")
    #expect(strings.text(.approve) == "承認")
    #expect(strings.text(.back) == "戻る")
    #expect(strings.text(.navigationTrail) == "移動履歴")
    #expect(strings.text(.connectionDiagnostics) == "接続診断")
    #expect(strings.text(.bridgeStatusPanel) == "バックエンド状態")
    #expect(strings.text(.bridgeReady) == "バックエンドは利用可能です")
    #expect(strings.text(.bridgeStarting) == "バックエンドは起動中です")
    #expect(strings.text(.bridgeNotConnected) == "バックエンドに未接続です")
    #expect(strings.text(.bridgeStartupFocus) == "起動優先")
    #expect(strings.text(.bridgeDisconnectedShort) == "バックエンド未接続")
    #expect(strings.text(.screenSummaryPending) == "起動後に読み込み")
    #expect(strings.text(.homeStartupSummary) == "バックエンドが未接続です。起動または再接続してから各画面を読み込みます。")
    #expect(strings.text(.debugCompatibilityTools) == "デバッグ互換ツール")
    #expect(strings.text(.debugCompatibilityToolsSummary) == "通常の macOS 操作導線から外し、必要時だけ開くブラウザ互換経路です")
    #expect(strings.text(.showDebugCompatibilityTools) == "デバッグ互換ツールを表示")
    #expect(strings.text(.hideDebugCompatibilityTools) == "デバッグ互換ツールを隠す")
    #expect(strings.text(.debugShell) == "ブラウザ互換シェル（デバッグ用）")
    #expect(strings.text(.debugShellCompatibilitySummary) == "通常操作ではなく、ブラウザでのデバッグ・互換確認・引き継ぎ用の経路です")
    #expect(strings.text(.bootstrapUI) == "デバッグ用互換URL")
    #expect(strings.text(.sessionProblem) == "バックエンドを復旧してください。起動後にこのアプリから再接続します。")
    #expect(strings.text(.bridgeStatusDetailDisconnected) == "バックエンドを起動すると各画面を読み込めます。macOS アプリから自動起動します")
    #expect(strings.text(.bridgeStatusPanelSummary) == "ここで接続状態を確認し、必要なら起動・再接続・ログ確認へ進みます。macOS アプリから自動起動します")
    #expect(strings.bridgeStartupSummary() == "起動または再接続してから各画面を読み込みます。")
    #expect(strings.bridgeTerminalRetentionSummary() == "macOS アプリから自動起動します。")
    #expect(strings.bridgeStatusDetailText(status: nil, version: nil, sourceUpdatedAt: nil) == "バックエンドを起動すると 起動または再接続してから各画面を読み込みます。 macOS アプリから自動起動します。")
    #expect(strings.bridgeStatusDetailText(status: "starting", version: "1.0.0", sourceUpdatedAt: nil) == "バックエンドは起動中です。macOS アプリから自動起動します。 バージョン: 1.0.0")
    #expect(strings.bridgeStatusPanelSummaryText(status: nil) == "まずここから 起動または再接続してから各画面を読み込みます。 macOS アプリから自動起動します。")
    #expect(strings.bridgeStatusPanelSummaryText(status: "starting").contains("バックエンドは起動中です"))
    #expect(strings.text(.bridgeStartedMessage) == "バックエンドを起動しました。このアプリで再接続します。")
    #expect(strings.text(.bridgeReconnectedMessage) == "バックエンドへ再接続しました。")
    #expect(strings.text(.bridgeRefreshedMessage) == "バックエンドの状態を更新しました。")
    #expect(strings.bridgeActionInProgressMessage(startingBridge: true) == "バックエンドを起動しています。ローカル接続が応答するまで少し待ってから再接続します。")
    #expect(strings.bridgeActionInProgressMessage(startingBridge: false) == "バックエンドへ再接続しています。接続診断とログを確認しながら待機します。")
    #expect(strings.bridgeLaunchWarmupMessage() == "バックエンドを起動しました。ローカル接続が応答するまで少し待ってから再接続します。")
    #expect(strings.bridgeRecoveryFailureMessage("mock failure").contains("run-app-local.log"))
    #expect(strings.localizedBridgeErrorMessage("Missing bearer token at /tmp/sayane-token") == "Bearer トークンが見つかりません: /tmp/sayane-token")
    #expect(strings.localizedBridgeErrorMessage("Could not connect to local Bridge") == "ローカルバックエンドに接続できません。")
    #expect(strings.localizedBridgeErrorMessage("Invalid Bridge response") == "バックエンドからの応答を解釈できません。")
    #expect(strings.localizedBridgeErrorMessage("HTTP 401: Missing or invalid resident app UI session") == "バックエンドから HTTP 401 が返りました: Resident App の UI セッションが見つからないか無効です")
    #expect(strings.localizedBridgeErrorMessage("Bridge launch failed: mock failure\nCheck the opened Bridge Terminal window or ~/.sayane/run-app-local.log.") == "バックエンドの起動に失敗しました: mock failure")
    #expect(strings.bridgeRecoveryHintTitle(issue: "missing_token") == "バックエンドトークンを確認")
    #expect(strings.bridgeRecoveryHintTitle(issue: "ui_session") == "バックエンドセッションを作り直す")
    #expect(strings.bridgeRecoveryHintTitle(issue: "not_connected") == "バックエンドを先に起動")
    #expect(strings.bridgeRecoveryIssueTitle(issue: "missing_token") == "バックエンドトークンが見つかりません")
    #expect(strings.bridgeRecoveryIssueTitle(issue: "ui_session") == "バックエンドセッションが無効です")
    #expect(strings.bridgeRecoveryIssueTitle(issue: "not_connected") == "バックエンドがまだ起動していません")
    #expect(strings.bridgeRecoveryIssueSummary(issue: "ui_session").contains("UI セッション"))
    #expect(strings.bridgeRecoveryStepMessages(issue: "missing_token", startupAvailable: true).count == 3)
    #expect(strings.bridgeRecoveryStepMessages(issue: "ui_session", startupAvailable: false).first == "まず再接続を実行して UI セッションを更新します。")
    #expect(strings.text(.openToken) == "トークンを開く")
    #expect(strings.text(.openLaunchSource) == "起動ソースを開く")
    #expect(strings.text(.copyHealthCommand) == "ヘルス確認コマンドをコピー")
    #expect(strings.text(.copyLaunchSource) == "起動ソースをコピー")
    #expect(strings.text(.copyStartupCommand) == "起動コマンドをコピー")
    #expect(strings.text(.copyDetail) == "詳細をコピー")
    #expect(strings.text(.copyDiff) == "差分をコピー")
    #expect(strings.text(.copyLineage) == "来歴をコピー")
    #expect(strings.text(.copyCurrentState) == "現在状態をコピー")
    #expect(strings.text(.copyRecoveryPreview) == "復旧プレビューをコピー")
    #expect(strings.text(.errorDetails) == "エラー詳細")
    #expect(strings.text(.showErrorDetails) == "エラー詳細を表示")
    #expect(strings.text(.hideErrorDetails) == "エラー詳細を隠す")
    #expect(strings.text(.copyOperatorSummary) == "運用サマリーをコピー")
    #expect(strings.text(.copyPhaseGates) == "フェーズゲートをコピー")
    #expect(strings.text(.copyReadSurfaces) == "参照先をコピー")
    #expect(strings.text(.copySuggestedActions) == "推奨アクションをコピー")
    #expect(strings.text(.exportHandoffNote) == "引き継ぎノートを書き出す")
    #expect(strings.text(.savedFile) == "保存しました")
    #expect(strings.text(.generatedAt) == "生成日時")
    #expect(strings.text(.bridgeContext) == "バックエンドコンテキスト")
    #expect(strings.text(.component) == "コンポーネント")
    #expect(strings.text(.statusDiagnostics) == "状態診断")
    #expect(strings.text(.returnCode) == "リターンコード")
    #expect(strings.text(.bridgeVersion) == "バージョン")
    #expect(strings.text(.sourceUpdatedAt) == "ソース更新時刻")
    #expect(strings.text(.healthEndpoint) == "ヘルスエンドポイント")
    #expect(strings.text(.tokenFile) == "トークンファイル")
    #expect(strings.text(.logFile) == "ログファイル")
    #expect(strings.text(.profile) == "プロファイル")
    #expect(strings.text(.tailLogs) == "ログ追跡コマンド")
    #expect(strings.text(.launchctlPrint) == "launchctl print")
    #expect(strings.text(.stdoutTail) == "stdout 追跡")
    #expect(strings.text(.stderrTail) == "stderr 追跡")
    #expect(strings.savedFileMessage(path: "/tmp/sample.txt") == "ファイル保存: /tmp/sample.txt")
    #expect(strings.tone(forCommand: "sayane app daemon-repair-preview --json") == .critical)
    #expect(strings.tone(forCommand: "launchctl print gui/501/example") == .positive)
    #expect(strings.commandPriorityTitle(for: "sayane app daemon-service-targets-status --json") == "確認ポイント")
    #expect(strings.text(.actionCompleted) == "完了")
    #expect(strings.text(.actionFailed) == "失敗")
    #expect(strings.text(.candidateResult) == "実行結果")
    #expect(strings.text(.resultForCurrentCandidate) == "この候補の最新結果")
    #expect(strings.text(.shortcutGuide) == "ショートカット")
    #expect(strings.text(.startHere) == "まずここから")
    #expect(strings.text(.noPriorityActions) == "今すぐ着手すべき項目はありません")
    #expect(strings.text(.noPriorityActionsDisconnected) == "最初にバックエンドを起動または再接続すると、この画面の優先項目を読み込めます")
    #expect(strings.text(.reviewNextCandidate) == "次の候補を確認")
    #expect(strings.text(.reviewDaemonAction) == "バックエンドの次アクションを確認")
    #expect(strings.text(.checkLaunchAgentStatus) == "LaunchAgentの状態を確認")
    #expect(strings.text(.openRunbook) == "運用手順書を開く")
    #expect(strings.text(.launchAgentFocus) == "LaunchAgent 注目点")
    #expect(strings.text(.launchAgentFocusSummary) == "現在状態・復旧プレビュー・次コマンドをまとめて確認します")
    #expect(strings.text(.currentStateDetails) == "現在状態の詳細")
    #expect(strings.text(.currentStateDetailsSummary) == "注目点の根拠をここで確認します")
    #expect(strings.text(.recoveryPreviewDetails) == "復旧プレビューの詳細")
    #expect(strings.text(.recoveryPreviewDetailsSummary) == "復旧要約の内訳と注意点を確認します")
    #expect(strings.text(.nextEpicWorkspace) == "次のエピック作業面")
    #expect(strings.text(.remainingWorkstreams) == "残りの判断面")
    #expect(strings.text(.remainingWorkstreamsSummary) == "優先導線で触れていない判断面だけを残します")
    #expect(strings.text(.priorityPathCoversCurrentWorkspace) == "現在の優先導線が主要な判断面をすでにカバーしています")
    #expect(strings.text(.operatorSummaryRail) == "運用サマリーレール")
    #expect(strings.text(.operatorSummaryRailSummary) == "現在のゲート・次コマンド・次の確認先をまとめて見ます")
    #expect(strings.text(.nextEpicWorkspaceSummary) == "次の判断面とブロッカーをまとめて確認します")
    #expect(strings.text(.operatorWorkspaceCompactSummary) == "重要な判断面を優先順とブロッカー付きで確認します")
    #expect(strings.text(.currentGate) == "現在のゲート")
    #expect(strings.text(.nextReadSurface) == "次の確認先")
    #expect(strings.text(.phaseClosureGates) == "フェーズ完了ゲート")
    #expect(strings.text(.phaseClosureGatesSummary) == "未完了ゲートと確認先を対応づけます")
    #expect(strings.text(.openSection) == "セクションを開く")
    #expect(strings.text(.nextCommand) == "次のコマンド")
    #expect(strings.text(.additionalBlockers) == "追加ブロッカー")
    #expect(strings.residentValueLabel("knowledge.preferences") == "知識 / 嗜好")
    #expect(strings.copiedCommandMessage(context: "フェーズ完了ゲート") == "コピーしました: フェーズ完了ゲート")
    #expect(strings.text(.evidenceDrilldown) == "根拠ドリルダウン")
    #expect(strings.text(.evidenceDrilldownSummary) == "関連する参照先を見比べて確認先を絞ります")
    #expect(strings.text(.decisionAssist) == "判断支援")
    #expect(strings.text(.decisionAssistSummary) == "次の一手を要約とコマンドで示します")
    #expect(strings.text(.inspectActionsSummary) == "現在の launchd 状態とバックエンドのヘルスを非破壊で確認します")
    #expect(strings.text(.recoverActionsSummary) == "cleanup / repair / bootout の順で古い状態を解消します")
    #expect(strings.text(.startActionsSummary) == "確認後に bootstrap / kickstart で起動します")
    #expect(strings.text(.logActionsSummary) == "ログの場所を確認してから tail で追跡します")
    #expect(strings.text(.statusSectionSummary) == "各運用面の状態・注目点・代表コマンドを確認します")
    #expect(strings.moreItemsMessage(3) == "ほか 3 件")
    #expect(strings.tone(forToken: "candidate_approved") == .neutral)
    #expect(strings.lineageDetailLabel("source_candidate_id") == "元候補ID")
    #expect(strings.text(.serviceControlAssistSummary) == "まずサービス制御境界を確認し、許可されたローカル制御を見極めます")
    #expect(strings.text(.launchAgentAssistRuntimeInit) == "runtime-init プレビューを先に確認します")
    #expect(strings.summaryCardLabel("packaging_model_decision") == "パッケージング判断")
    #expect(strings.summaryCardLabel("service_integration_line") == "サービス統合")
    #expect(strings.summaryCardLabel("supervision_ux_line") == "監視体験判断")
    #expect(strings.summaryCardLabel("recovery_and_consent_line") == "復旧と同意")
    #expect(strings.summaryCardLabel("service_control_boundary_definition") == "サービス制御境界")
    #expect(strings.summaryCardLabel("supported_packaging_model_finalized") == "サポートするパッケージング判断")
    #expect(strings.tokenLabel("baseline_contract_implemented") == "契約ベースライン実装済み")
    #expect(strings.tokenLabel("blocked") == "ブロック中")
    #expect(strings.tokenLabel("candidate_requires_larger_architecture_change") == "大きな設計変更が必要")
    #expect(strings.tokenLabel("native_macos_app_primary") == "macOS ネイティブアプリ")
    #expect(strings.tokenLabel("local_bridge_shell_primary") == "ローカルバックエンドシェル")
    #expect(strings.tokenLabel("bridge_hosted_debug_shell") == "バックエンド上の互換シェル")
    #expect(strings.tokenLabel("service_first_resident_runtime") == "service-first 常駐ランタイム候補")
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
@Test func appModelResolvesLocalCommandPaths() {
    let model = AppModel()

    let relative = model.resolvedLocalCommandPath("./scripts/run-macos-app-preview.sh")
    #expect(relative?.hasSuffix("/scripts/run-macos-app-preview.sh") == true)

    let absolute = model.resolvedLocalCommandPath("/Users/tomyuk/Projects/Sayane/sayane/scripts/run-app-local.sh")
    #expect(absolute == "/Users/tomyuk/Projects/Sayane/sayane/scripts/run-app-local.sh")

    #expect(model.resolvedLocalCommandPath("sayane serve --host 127.0.0.1 --port 38741") == nil)
    #expect(model.resolvedLocalCommandPath("./scripts/not-found.sh") == nil)
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
    #expect(model.bridgeStatusHeadline == "バックエンドに未接続です")
    #expect(model.bridgeSuggestedActionText == "バックエンドを起動")
    #expect(model.bridgeStatusDetail.contains("macOS アプリから自動起動"))
    #expect(model.bridgeStatusPanelSummaryText == "まずここから 起動または再接続してから各画面を読み込みます。 macOS アプリから自動起動します。")
    #expect(model.homeBridgeSummaryText == "バックエンドが未接続です。起動または再接続してから各画面を読み込みます。")
    #expect(model.homePriorityEmptyMessage == "最初にバックエンドを起動または再接続すると、この画面の優先項目を読み込めます")
    #expect(model.homePriorityEmptyBadgeText == "起動優先")
    #expect(model.queueEmptyMessage == "最初にバックエンドを起動または再接続すると、この画面の優先項目を読み込めます")
    #expect(model.queueEmptyBadgeText == "起動優先")
    #expect(model.detailEmptyMessage == "最初にバックエンドを起動または再接続すると、この画面の優先項目を読み込めます")
    #expect(model.detailEmptyBadgeText == "起動優先")
    #expect(model.daemonWorkspaceEmptyMessage == "最初にバックエンドを起動または再接続すると、この画面の優先項目を読み込めます")
    #expect(model.daemonWorkspaceEmptyBadgeText == "起動優先")
    #expect(model.daemonSummaryEmptyMessage == "最初にバックエンドを起動または再接続すると、この画面の優先項目を読み込めます")
    #expect(model.daemonSummaryEmptyBadgeText == "起動優先")
    #expect(model.bridgeDiagnosticRows(compact: true).map(\.label) == ["ヘルスエンドポイント", "起動ソース", "トークンファイル", "ログファイル"])
    #expect(model.bridgeNeedsExpandedRecoveryLayout)
    #expect(model.bridgeRecoveryActionDisabled == false)
    #expect(model.bridgeRecoveryInProgress == false)
    #expect(model.actionShowsProgress == false)

    model.health = HealthResponse(status: "starting", version: "1.0.0", sourceUpdatedAt: nil, component: nil)
    #expect(model.bridgeStatusHeadline == "バックエンドは起動中です")
    #expect(model.bridgeStatusDetail == "バックエンドは起動中です。macOS アプリから自動起動します。 バージョン: 1.0.0")
    #expect(model.bridgeStatusPanelSummaryText.contains("バックエンドは起動中です"))
    #expect(model.bridgeDiagnosticRows(compact: true).map(\.label) == ["ヘルスエンドポイント", "起動ソース", "トークンファイル", "ログファイル"])
    #expect(model.bridgeSuggestedActionText == "再試行")

    model.health = HealthResponse(status: "ok", version: "1.0.1", sourceUpdatedAt: "2026-06-23T09:00:00Z", component: nil)
    #expect(model.bridgeStatusHeadline == "バックエンドは利用可能です")
    #expect(model.bridgeStatusDetail.contains("1.0.1"))
    #expect(model.bridgeStatusPanelSummaryText == "ここで接続状態を確認し、必要なら起動・再接続・ログ確認へ進みます。macOS アプリから自動起動します。")
    #expect(model.homeBridgeSummaryText == "バックエンド接続: 利用可能です · 1.0.1")
    #expect(model.homePriorityEmptyMessage == "今すぐ着手すべき項目はありません")
    #expect(model.homePriorityEmptyBadgeText == "正常シグナル")
    #expect(model.queueEmptyMessage == "候補はまだありません")
    #expect(model.queueEmptyBadgeText == nil)
    #expect(model.detailEmptyMessage == "候補を選ぶと、詳細・差分・来歴を表示します")
    #expect(model.detailEmptyBadgeText == "候補キュー")
    #expect(model.daemonWorkspaceEmptyMessage == "今すぐ着手すべき項目はありません")
    #expect(model.daemonWorkspaceEmptyBadgeText == nil)
    #expect(model.daemonSummaryEmptyMessage == "今すぐ着手すべき項目はありません")
    #expect(model.daemonSummaryEmptyBadgeText == nil)
    #expect(model.bridgeDiagnosticRows(compact: true).map(\.label) == ["バックエンド URL", "ヘルスエンドポイント", "起動ソース", "プロファイル"])
    #expect(model.bridgeDiagnosticRows(compact: false).map(\.label) == ["バックエンド URL", "ヘルスエンドポイント", "起動ソース", "プロファイル"])
    #expect(model.bridgeDebugDiagnosticRows().map(\.label).contains("デバッグ用互換URL"))
    #expect(model.bridgeNeedsExpandedRecoveryLayout == false)
    #expect(model.bridgeSuggestedActionText == "更新")
    #expect(model.toolbarRefreshText == "更新")

    model.lastBridgeLaunchFailure = "Bridge launch failed: Missing launcher script: /tmp/missing"
    #expect(model.bridgeDiagnosticRows(compact: true).map(\.label).contains("直近の起動失敗"))
    #expect(model.launchSourcePath() != nil)

    model.isLoading = true
    #expect(model.bridgeRecoveryActionDisabled == true)
    #expect(model.bridgeRecoveryInProgress == true)
    #expect(model.bridgeSuggestedActionText == "更新中…")
    #expect(model.toolbarRefreshText == "更新中…")

    model.health = nil
    #expect(model.bridgeSuggestedActionText == "バックエンド起動中…")
    #expect(model.toolbarRefreshText == "バックエンド起動中…")

    model.health = HealthResponse(status: "starting", version: "1.0.0", sourceUpdatedAt: nil, component: nil)
    #expect(model.bridgeSuggestedActionText == "再接続中…")
    #expect(model.toolbarRefreshText == "再接続中…")
}

@MainActor
@Test func appModelHidesRecoveredBridgeFailureBannerWhenHealthy() {
    let model = AppModel()
    model.health = HealthResponse(status: "ok", version: "1.0.14", sourceUpdatedAt: nil, component: "resident-app-bridge")
    model.actionTitle = model.strings.text(.actionFailed)
    model.actionMessage = model.strings.text(.sessionProblem)
    model.actionTone = .critical

    #expect(model.shouldShowActionFeedbackBanner == false)
}

@MainActor
@Test func appModelBuildsBridgeRecoveryGuidance() {
    let model = AppModel()

    model.errorMessage = "Could not connect to local Bridge"
    #expect(model.errorDisplayMessage == "ローカルバックエンドに接続できません。")
    #expect(model.bridgeRecoveryIssueTitle == "バックエンドがまだ起動していません")
    #expect(model.bridgeRecoveryIssueSummary == "バックエンドの待受がまだ無いため、起動または再接続してから各画面を読み込みます。")
    #expect(model.bridgeRecoveryHintTitle == "バックエンドを先に起動")
    #expect(model.bridgeRecoveryStepMessages.first == "バックエンドがまだ待受していません。")
    #expect(model.bridgeRecoveryShowsTokenAction == false)
    #expect(model.bridgeRecoveryPrefersLauncherAction == false)
    #expect(model.shouldExposeDebugCompatibilityTools == false)
    #expect(model.shouldPresentBlockingErrorView == false)

    model.errorMessage = "Missing bearer token at /tmp/sayane-token"
    #expect(model.errorDisplayMessage == "Bearer トークンが見つかりません: /tmp/sayane-token")
    #expect(model.bridgeRecoveryIssueTitle == "バックエンドトークンが見つかりません")
    #expect(model.bridgeRecoveryHintTitle == "バックエンドトークンを確認")
    #expect(model.bridgeRecoveryShowsTokenAction)
    #expect(model.bridgeRecoveryPrefersTokenAction)
    #expect(model.shouldExposeDebugCompatibilityTools == false)

    model.errorMessage = "HTTP 401: Missing or invalid resident app UI セッション"
    #expect(model.errorDisplayMessage?.contains("バックエンドから HTTP 401 が返りました") == true)
    #expect(model.bridgeRecoveryIssueTitle == "バックエンドセッションが無効です")
    #expect(model.bridgeRecoveryHintTitle == "バックエンドセッションを作り直す")
    #expect(model.bridgeRecoveryShowsTokenAction)
    #expect(model.bridgeRecoveryPrefersTokenAction == false)
    #expect(model.bridgeRecoveryStepMessages.contains("まず再接続を実行して UI セッションを更新します。"))
    #expect(model.shouldExposeDebugCompatibilityTools == false)

    model.lastBridgeLaunchFailure = "Backend launch failed: mock failure"
    #expect(model.shouldExposeDebugCompatibilityTools == false)

    model.hasLoadedInitialData = true
    #expect(model.shouldPresentBlockingErrorView)

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
      "preflight": {},
      "readiness_diagnostics": [],
      "proof_diagnostics": [],
      "vault_status": {}
    }
    """#.utf8)
    model.daemonState = try! JSONDecoder().decode(DaemonPanelScreenState.self, from: daemonData)
    #expect(model.hasDebugCompatibilitySurface)
    #expect(model.shouldExposeDebugCompatibilityTools)
    #expect(model.shouldIncludeDebugCompatibilityInHandoff)
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
@Test func appModelPrefersLauncherActionWhenStartupScriptIsLocal() throws {
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
        "current_supported_operator_path": {"startup_command_text": "./scripts/run-app-local.sh --terminal", "bootstrap_ui": "http://127.0.0.1:38741/app/ui", "local_only": true, "notes": []},
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
    model.errorMessage = "Could not connect to local Bridge"

    #expect(model.bridgeRecoveryShowsLauncherAction)
    #expect(model.bridgeRecoveryPrefersLauncherAction)
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
    #expect(model.nextDaemonReasonText == "フェーズ完了を妨げるブロッカーを確認します。")
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
    #expect(config.debugShellEntryURL(token: "abc").absoluteString.contains("bootstrap_token=abc"))
    #expect(config.debugShellEntryURL(token: nil).absoluteString == "http://127.0.0.1:38741/app/ui")
}

@Test func bridgeLauncherLaunchFailedMentionsTerminalAndLog() {
    let error = BridgeLauncherError.launchFailed("mock failure")
    let description = error.errorDescription ?? ""
    #expect(description.contains("Backend launch failed: mock failure"))
    #expect(description.contains("run-app-local.log"))
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
    #expect(gates.contains("パッケージング判断が文書化されている"))
    #expect(gates.contains("未解決ブロッカー: 別計画が必要"))

    let readSurfaces = try #require(model.daemonReadSurfacesClipboardText())
    #expect(readSurfaces.contains("1. sayane app daemon-operator-phase-status --json"))

    let suggestedActions = try #require(model.daemonSuggestedActionsClipboardText())
    #expect(suggestedActions.contains("推奨アクション"))
    #expect(suggestedActions.contains("フェーズ完了を妨げるブロッカーを確認します。"))

    let handoff = try #require(model.daemonHandoffExportText())
    #expect(handoff.contains("引き継ぎスナップショット"))
    #expect(handoff.contains("バックエンドコンテキスト:"))
    #expect(handoff.contains("生成日時: "))
    #expect(handoff.contains("プロファイル: default"))
    #expect(handoff.contains("バックエンド URL: http://127.0.0.1:38741"))
    #expect(handoff.contains("ヘルスエンドポイント: http://127.0.0.1:38741/health"))
    #expect(handoff.contains("ブラウザ互換シェル（デバッグ用）: http://127.0.0.1:38741/app/ui") == false)
    #expect(handoff.contains("トークンファイル: "))
    #expect(handoff.contains(".sayane/bridge.token"))
    #expect(handoff.contains("ログファイル: "))
    #expect(handoff.contains(".sayane/run-app-local.log"))
    #expect(handoff.contains("バックエンド状態: バックエンドは利用可能です"))
    #expect(handoff.contains("コンポーネント: resident-app-bridge"))
    #expect(handoff.contains("バージョン: 1.0.12"))
    #expect(handoff.contains("ソース更新時刻: 2026-06-24T10:00:00Z"))
    #expect(handoff.contains("状態診断:"))
    #expect(handoff.contains("• 次のコマンド: sayane app daemon-operator-phase-status --json"))
    #expect(handoff.contains("• 理由: フェーズ完了を妨げるブロッカーを確認します。"))
    #expect(handoff.contains("• launchctl print: launchctl print gui/501/io.sayane.bridge"))
    #expect(handoff.contains("ログ追跡コマンド:"))
    #expect(handoff.contains("• stdout 追跡: tail -f /tmp/sayane/stdout.log"))
    #expect(handoff.contains("• stderr 追跡: tail -f /tmp/sayane/stderr.log"))
    #expect(handoff.contains("事前確認:"))
    #expect(handoff.contains("• sayane app daemon-preflight --json"))
    #expect(handoff.contains("根拠診断:"))
    #expect(handoff.contains("• sayane app daemon-proof-diagnostics --operation-class bridge_health --json"))
    #expect(handoff.contains("運用サマリーレール:"))
    #expect(handoff.contains("フェーズ完了ゲート:"))
    #expect(handoff.contains("推奨アクション:"))
    #expect(handoff.contains("参照サーフェス:"))
    #expect(handoff.contains("現在状態:"))
    #expect(handoff.contains("復旧プレビュー:"))
    let operatorSummaryIndex = try #require(handoff.range(of: "運用サマリーレール:")?.lowerBound)
    let bridgeContextIndex = try #require(handoff.range(of: "バックエンドコンテキスト:")?.lowerBound)
    let suggestedActionIndex = try #require(handoff.range(of: "推奨アクション:")?.lowerBound)
    let phaseGatesIndex = try #require(handoff.range(of: "フェーズ完了ゲート:")?.lowerBound)
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
@Test func routineHealthyHandoffOmitsDebugCompatibilityURL() throws {
    let model = AppModel()
    model.health = HealthResponse(status: "ok", version: "1.0.14", sourceUpdatedAt: nil, component: "resident-app-bridge")

    let daemonData = Data(#"""
    {
      "kind": "resident_app_daemon_panel_screen_state",
      "summary_cards": [],
      "operator_panels": [],
      "service_target_summary": {"current_platform": null, "recommended_target": null, "targets": []},
      "launchagent_summary": {"preview_available": false, "status_available": false, "plist_path": null, "loaded_status": null, "launchctl_commands": {}},
      "operator_phase_summary": {"phase": null, "phase_status": null, "phase_readiness": "ready", "blocking_reasons": [], "checklist": []},
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

    #expect(model.hasDebugCompatibilitySurface)
    #expect(model.shouldExposeDebugCompatibilityTools == false)
    #expect(model.shouldIncludeDebugCompatibilityInHandoff == false)

    let handoff = try #require(model.daemonHandoffExportText())
    #expect(handoff.contains("バックエンド URL: http://127.0.0.1:38741"))
    #expect(handoff.contains("ヘルスエンドポイント: http://127.0.0.1:38741/health"))
    #expect(handoff.contains("ブラウザ互換シェル（デバッグ用）") == false)
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
    #expect(model.navigationTrailText == "ホーム → バックエンド状態")

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
    let disconnected = model.sidebarMetadata(for: .home)
    #expect(disconnected.title == "ホーム")
    #expect(disconnected.summary == "起動後に読み込み")
    #expect(disconnected.badgeText == "バックエンド未接続")
    #expect(disconnected.badgeTone == .neutral)
    #expect(model.shouldCondenseChromeMetadata)
    #expect(model.shouldShowNavigationTrailInStatusBar == false)
    #expect(model.shouldShowSelectedCandidateInStatusBar == false)

    model.hasLoadedInitialData = true
    model.homeState = HomeScreenState(
        kind: "resident_app_home_screen_state",
        summaryCards: [],
        topReviewItems: [
            TopReviewItem(candidateId: "cand-home-1", status: "pending", proposalSection: nil, displaySummary: nil, requiresReview: true),
        ],
        topDaemonActions: [],
        vaultSummary: nil,
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
    #expect(model.shouldCondenseChromeMetadata == false)
    #expect(model.shouldShowNavigationTrailInStatusBar)
    #expect(model.shouldShowSelectedCandidateInStatusBar)

    let queue = model.sidebarMetadata(for: .queue)
    #expect(queue.title == "候補キュー")
    #expect(queue.summary == "レビュー対象: 3")
    #expect(queue.badgeText == "3")
    #expect(queue.badgeTone == .caution)

    let daemon = model.sidebarMetadata(for: .daemon)
    #expect(daemon.title == "バックエンド状態")
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
