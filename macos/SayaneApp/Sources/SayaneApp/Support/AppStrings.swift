import Foundation

struct AppStrings {
    enum Language {
        case ja
        case en
    }

    let language: Language

    static let current = AppStrings(
        language: Locale.preferredLanguages.first?.lowercased().hasPrefix("ja") == true ? .ja : .en
    )

    private static func lowercasedFirstLetter(_ value: String) -> String {
        guard let first = value.first else { return value }
        return String(first).lowercased() + value.dropFirst()
    }

    private static func removingPrefix(_ prefix: String, from value: String) -> String? {
        guard value.hasPrefix(prefix) else { return nil }
        return String(value.dropFirst(prefix.count))
    }

    func text(_ key: Key) -> String {
        switch (language, key) {
        case (.ja, .appTitle): return "紗綾音"
        case (.en, .appTitle): return "紗綾音"
        case (.ja, .home): return "ホーム"
        case (.en, .home): return "Home"
        case (.ja, .queue): return "候補キュー"
        case (.en, .queue): return "Candidate Queue"
        case (.ja, .daemon): return "バックエンド状態"
        case (.en, .daemon): return "Backend State"
        case (.ja, .refresh): return "更新"
        case (.en, .refresh): return "Refresh"
        case (.ja, .refreshInProgress): return "更新中…"
        case (.en, .refreshInProgress): return "Refreshing…"
        case (.ja, .retry): return "再試行"
        case (.en, .retry): return "Retry"
        case (.ja, .bootstrap): return "再接続"
        case (.en, .bootstrap): return "Reconnect"
        case (.ja, .bootstrapInProgress): return "再接続中…"
        case (.en, .bootstrapInProgress): return "Reconnecting…"
        case (.ja, .captureClipboard): return "クリップボードを取り込む"
        case (.en, .captureClipboard): return "Capture Clipboard"
        case (.ja, .openLogs): return "ログを開く"
        case (.en, .openLogs): return "Open Logs"
        case (.ja, .startBridge): return "バックエンドを起動"
        case (.en, .startBridge): return "Start Backend"
        case (.ja, .startBridgeInProgress): return "バックエンド起動中…"
        case (.en, .startBridgeInProgress): return "Starting Backend…"
        case (.ja, .status): return "状態"
        case (.en, .status): return "Status"
        case (.ja, .nextActions): return "次のアクション"
        case (.en, .nextActions): return "Next Actions"
        case (.ja, .summaryCards): return "サマリー"
        case (.en, .summaryCards): return "Summary"
        case (.ja, .topReviewItems): return "レビュー候補"
        case (.en, .topReviewItems): return "Top Review Items"
        case (.ja, .topDaemonActions): return "バックエンドの次アクション"
        case (.en, .topDaemonActions): return "Top Backend Actions"
        case (.ja, .reviewableCount): return "レビュー対象"
        case (.en, .reviewableCount): return "Reviewable"
        case (.ja, .localVault): return "Local Vault"
        case (.en, .localVault): return "Local Vault"
        case (.ja, .vaultPath): return "Vaultパス"
        case (.en, .vaultPath): return "Vault Path"
        case (.ja, .vaultSessions): return "アンロックセッション"
        case (.en, .vaultSessions): return "Unlock Session"
        case (.ja, .activeSessions): return "有効セッション"
        case (.en, .activeSessions): return "Active Sessions"
        case (.ja, .sessionPurpose): return "利用目的"
        case (.en, .sessionPurpose): return "Purpose"
        case (.ja, .expiresAt): return "有効期限"
        case (.en, .expiresAt): return "Expires At"
        case (.ja, .idleExpiresAt): return "アイドル期限"
        case (.en, .idleExpiresAt): return "Idle Expires At"
        case (.ja, .unlockNormal): return "通常を開く"
        case (.en, .unlockNormal): return "Open Normal"
        case (.ja, .unlockSensitive): return "要保護を開く"
        case (.en, .unlockSensitive): return "Open Sensitive"
        case (.ja, .unlockDeepPrivate): return "厳重秘匿を開く"
        case (.en, .unlockDeepPrivate): return "Open Deep Private"
        case (.ja, .lockAll): return "すべてロック"
        case (.en, .lockAll): return "Lock All"
        case (.ja, .unlockPolicies): return "アンロックポリシー"
        case (.en, .unlockPolicies): return "Unlock Policies"
        case (.ja, .recommendedSetup): return "推奨セットアップ"
        case (.en, .recommendedSetup): return "Recommended Setup"
        case (.ja, .supported): return "対応"
        case (.en, .supported): return "Supported"
        case (.ja, .notSupported): return "未対応"
        case (.en, .notSupported): return "Not Supported"
        case (.ja, .vaultUnavailable): return "Local Vault はまだ通常ランタイムに接続されていません"
        case (.en, .vaultUnavailable): return "Local Vault is not connected to the routine runtime yet"
        case (.ja, .backend): return "バックエンド"
        case (.en, .backend): return "Backend"
        case (.ja, .statusCounts): return "状態集計"
        case (.en, .statusCounts): return "Status Counts"
        case (.ja, .topSections): return "上位セクション"
        case (.en, .topSections): return "Top Sections"
        case (.ja, .detail): return "候補詳細"
        case (.en, .detail): return "Candidate Detail"
        case (.ja, .actionAvailability): return "利用可能な操作"
        case (.en, .actionAvailability): return "Available Actions"
        case (.ja, .proposal): return "提案内容"
        case (.en, .proposal): return "Proposal"
        case (.ja, .evaluation): return "評価内容"
        case (.en, .evaluation): return "Evaluation"
        case (.ja, .capturedText): return "取り込みテキスト"
        case (.en, .capturedText): return "Captured Text"
        case (.ja, .diff): return "差分"
        case (.en, .diff): return "Diff"
        case (.ja, .lineage): return "来歴"
        case (.en, .lineage): return "Lineage"
        case (.ja, .evaluate): return "評価"
        case (.en, .evaluate): return "Evaluate"
        case (.ja, .approve): return "承認"
        case (.en, .approve): return "Approve"
        case (.ja, .reject): return "却下"
        case (.en, .reject): return "Reject"
        case (.ja, .revise): return "修正"
        case (.en, .revise): return "Revise"
        case (.ja, .operatorPhase): return "運用フェーズ"
        case (.en, .operatorPhase): return "Operator Phase"
        case (.ja, .serviceTargets): return "サービス対象"
        case (.en, .serviceTargets): return "Service Targets"
        case (.ja, .launchAgent): return "LaunchAgent"
        case (.en, .launchAgent): return "LaunchAgent"
        case (.ja, .clipboardEmpty): return "クリップボードにテキストがありません。"
        case (.en, .clipboardEmpty): return "No text is available in the clipboard."
        case (.ja, .connectionProblem): return "バックエンドに接続できません。"
        case (.en, .connectionProblem): return "Could not connect to the backend."
        case (.ja, .sessionProblem): return "バックエンドを復旧してください。起動後にこのアプリから再接続します。"
        case (.en, .sessionProblem): return "Recover the local backend, then reconnect from this app."
        case (.ja, .loading): return "読み込み中…"
        case (.en, .loading): return "Loading…"
        case (.ja, .none): return "なし"
        case (.en, .none): return "None"
        case (.ja, .error): return "エラー"
        case (.en, .error): return "Error"
        case (.ja, .bridgeHealthy): return "バックエンド接続"
        case (.en, .bridgeHealthy): return "Backend Health"
        case (.ja, .bridgeStartupFocus): return "起動優先"
        case (.en, .bridgeStartupFocus): return "Startup First"
        case (.ja, .bridgeDisconnectedShort): return "バックエンド未接続"
        case (.en, .bridgeDisconnectedShort): return "Backend Disconnected"
        case (.ja, .screenSummaryPending): return "起動後に読み込み"
        case (.en, .screenSummaryPending): return "Loads after startup"
        case (.ja, .homeStartupSummary): return "バックエンドが未接続です。起動または再接続してから各画面を読み込みます。"
        case (.en, .homeStartupSummary): return "The backend is disconnected. Start or reconnect first, then load the Home, Queue, and Backend State screens."
        case (.ja, .currentCandidate): return "選択中候補"
        case (.en, .currentCandidate): return "Selected Candidate"
        case (.ja, .editedText): return "修正文"
        case (.en, .editedText): return "Edited Text"
        case (.ja, .changeReason): return "変更理由"
        case (.en, .changeReason): return "Change Reason"
        case (.ja, .rejectReason): return "却下理由"
        case (.en, .rejectReason): return "Reject Reason"
        case (.ja, .evaluateLevel): return "評価レベル"
        case (.en, .evaluateLevel): return "Evaluation Level"
        case (.ja, .submit): return "実行"
        case (.en, .submit): return "Submit"
        case (.ja, .cancel): return "キャンセル"
        case (.en, .cancel): return "Cancel"
        case (.ja, .supportedPath): return "現在の運用経路"
        case (.en, .supportedPath): return "Current Supported Path"
        case (.ja, .exitCriteria): return "完了条件"
        case (.en, .exitCriteria): return "Exit Criteria"
        case (.ja, .notInScope): return "対象外"
        case (.en, .notInScope): return "Not In Scope"
        case (.ja, .copyCommand): return "コマンドをコピー"
        case (.en, .copyCommand): return "Copy Command"
        case (.ja, .copyDetail): return "詳細をコピー"
        case (.en, .copyDetail): return "Copy Detail"
        case (.ja, .copyDiff): return "差分をコピー"
        case (.en, .copyDiff): return "Copy Diff"
        case (.ja, .copyLineage): return "来歴をコピー"
        case (.en, .copyLineage): return "Copy Lineage"
        case (.ja, .copyCurrentState): return "現在状態をコピー"
        case (.en, .copyCurrentState): return "Copy Current State"
        case (.ja, .copyRecoveryPreview): return "復旧プレビューをコピー"
        case (.en, .copyRecoveryPreview): return "Copy Recovery Preview"
        case (.ja, .copyOperatorSummary): return "運用サマリーをコピー"
        case (.en, .copyOperatorSummary): return "Copy Operator Summary"
        case (.ja, .copyPhaseGates): return "フェーズゲートをコピー"
        case (.en, .copyPhaseGates): return "Copy Phase Gates"
        case (.ja, .copyReadSurfaces): return "参照先をコピー"
        case (.en, .copyReadSurfaces): return "Copy Read Surfaces"
        case (.ja, .copySuggestedActions): return "推奨アクションをコピー"
        case (.en, .copySuggestedActions): return "Copy Suggested Actions"
        case (.ja, .exportHandoffNote): return "引き継ぎノートを書き出す"
        case (.en, .exportHandoffNote): return "Export Handoff Note"
        case (.ja, .copiedCommand): return "コピーしました"
        case (.en, .copiedCommand): return "Copied"
        case (.ja, .actionCompleted): return "完了"
        case (.en, .actionCompleted): return "Completed"
        case (.ja, .savedFile): return "保存しました"
        case (.en, .savedFile): return "Saved"
        case (.ja, .actionFailed): return "失敗"
        case (.en, .actionFailed): return "Failed"
        case (.ja, .bridgeStartedMessage): return "バックエンドを起動しました。このアプリで再接続します。"
        case (.en, .bridgeStartedMessage): return "Started the backend and reconnected from this app."
        case (.ja, .bridgeReconnectedMessage): return "バックエンドへ再接続しました。"
        case (.en, .bridgeReconnectedMessage): return "Reconnected to the backend."
        case (.ja, .bridgeRefreshedMessage): return "バックエンドの状態を更新しました。"
        case (.en, .bridgeRefreshedMessage): return "Refreshed the backend state."
        case (.ja, .openPlist): return "plistファイルを開く"
        case (.en, .openPlist): return "Open Plist"
        case (.ja, .openRuntime): return "ランタイムを開く"
        case (.en, .openRuntime): return "Open Runtime"
        case (.ja, .openLauncher): return "ランチャーを開く"
        case (.en, .openLauncher): return "Open Launcher"
        case (.ja, .reviewPreviews): return "復旧プレビュー"
        case (.en, .reviewPreviews): return "Recovery Previews"
        case (.ja, .generatedAt): return "生成日時"
        case (.en, .generatedAt): return "Generated At"
        case (.ja, .bridgeContext): return "バックエンドコンテキスト"
        case (.en, .bridgeContext): return "Backend Context"
        case (.ja, .component): return "コンポーネント"
        case (.en, .component): return "Component"
        case (.ja, .currentState): return "現在状態"
        case (.en, .currentState): return "Current State"
        case (.ja, .reason): return "理由"
        case (.en, .reason): return "Reason"
        case (.ja, .notes): return "メモ"
        case (.en, .notes): return "Notes"
        case (.ja, .scope): return "対象範囲"
        case (.en, .scope): return "Scope"
        case (.ja, .recommended): return "推奨"
        case (.en, .recommended): return "Recommended"
        case (.ja, .errorDetails): return "エラー詳細"
        case (.en, .errorDetails): return "Error Details"
        case (.ja, .showErrorDetails): return "エラー詳細を表示"
        case (.en, .showErrorDetails): return "Show Error Details"
        case (.ja, .hideErrorDetails): return "エラー詳細を隠す"
        case (.en, .hideErrorDetails): return "Hide Error Details"
        case (.ja, .currentPlatform): return "現在のプラットフォーム"
        case (.en, .currentPlatform): return "Current Platform"
        case (.ja, .loadedStatus): return "読み込み状態"
        case (.en, .loadedStatus): return "Loaded Status"
        case (.ja, .packagingModels): return "パッケージング候補"
        case (.en, .packagingModels): return "Packaging Models"
        case (.ja, .primaryOperatorUI): return "主要オペレーターUI"
        case (.en, .primaryOperatorUI): return "Primary Operator UI"
        case (.ja, .recommendedLauncher): return "推奨ランチャー"
        case (.en, .recommendedLauncher): return "Recommended Launcher"
        case (.ja, .operatorSurfaceNotes): return "運用サーフェス補足"
        case (.en, .operatorSurfaceNotes): return "Operator Surface Notes"
        case (.ja, .supervision): return "監視体験"
        case (.en, .supervision): return "Supervision UX"
        case (.ja, .recoveryPolicy): return "復旧ポリシー"
        case (.en, .recoveryPolicy): return "Recovery Policy"
        case (.ja, .backgroundSurfaces): return "背景サーフェス"
        case (.en, .backgroundSurfaces): return "Background Surfaces"
        case (.ja, .guardrails): return "ガードレール"
        case (.en, .guardrails): return "Guardrails"
        case (.ja, .blockedBy): return "未解決ブロッカー"
        case (.en, .blockedBy): return "Blocked By"
        case (.ja, .nextCommand): return "次のコマンド"
        case (.en, .nextCommand): return "Next Command"
        case (.ja, .additionalBlockers): return "追加ブロッカー"
        case (.en, .additionalBlockers): return "Additional Blockers"
        case (.ja, .allowedCommands): return "許可コマンド"
        case (.en, .allowedCommands): return "Allowed Commands"
        case (.ja, .deferredCommands): return "保留コマンド"
        case (.en, .deferredCommands): return "Deferred Commands"
        case (.ja, .recoveryFlow): return "推奨復旧フロー"
        case (.en, .recoveryFlow): return "Recommended Recovery Flow"
        case (.ja, .passiveVisibility): return "受動可視化"
        case (.en, .passiveVisibility): return "Passive Visibility"
        case (.ja, .activeSupervision): return "能動制御"
        case (.en, .activeSupervision): return "Active Supervision"
        case (.ja, .startupVisibility): return "起動可視化"
        case (.en, .startupVisibility): return "Startup Visibility"
        case (.ja, .phaseChecklist): return "フェーズ完了チェック"
        case (.en, .phaseChecklist): return "Phase Closure Checklist"
        case (.ja, .readSurfaces): return "参照サーフェス"
        case (.en, .readSurfaces): return "Read Surfaces"
        case (.ja, .localOnly): return "ローカル限定"
        case (.en, .localOnly): return "Local Only"
        case (.ja, .statusValue): return "状態"
        case (.en, .statusValue): return "Status"
        case (.ja, .startupCommand): return "起動コマンド"
        case (.en, .startupCommand): return "Startup Command"
        case (.ja, .bootstrapUI): return "デバッグ用互換URL"
        case (.en, .bootstrapUI): return "Debug Compatibility URL"
        case (.ja, .handoffSnapshot): return "引き継ぎスナップショット"
        case (.en, .handoffSnapshot): return "Handoff Snapshot"
        case (.ja, .workstreams): return "ワークストリーム"
        case (.en, .workstreams): return "Workstreams"
        case (.ja, .platformScope): return "対象プラットフォーム"
        case (.en, .platformScope): return "Platform Scope"
        case (.ja, .operatorValue): return "運用価値"
        case (.en, .operatorValue): return "Operator Value"
        case (.ja, .implementationOrder): return "推奨実装順"
        case (.en, .implementationOrder): return "Recommended Implementation Order"
        case (.ja, .serviceLifecycle): return "サービスライフサイクル"
        case (.en, .serviceLifecycle): return "Service Lifecycle"
        case (.ja, .policyGates): return "ポリシーゲート"
        case (.en, .policyGates): return "Policy Gates"
        case (.ja, .governingRules): return "運用ルール"
        case (.en, .governingRules): return "Governing Rules"
        case (.ja, .appUIPolicy): return "アプリUIポリシー"
        case (.en, .appUIPolicy): return "App UI Policy"
        case (.ja, .allowedReads): return "許可された参照"
        case (.en, .allowedReads): return "Allowed Reads"
        case (.ja, .allowedWrites): return "許可された書き込み"
        case (.en, .allowedWrites): return "Allowed Writes"
        case (.ja, .allowedControlExposure): return "許可された制御公開"
        case (.en, .allowedControlExposure): return "Allowed Control Exposure"
        case (.ja, .forbiddenExposure): return "禁止された制御公開"
        case (.en, .forbiddenExposure): return "Forbidden Exposure"
        case (.ja, .platformTargets): return "対象サービス"
        case (.en, .platformTargets): return "Platform Targets"
        case (.ja, .rollbackRequired): return "ロールバック必須"
        case (.en, .rollbackRequired): return "Rollback Required"
        case (.ja, .policyRequired): return "ポリシー必須"
        case (.en, .policyRequired): return "Policy Required"
        case (.ja, .launchAgentRunbook): return "LaunchAgent 運用手順書"
        case (.en, .launchAgentRunbook): return "LaunchAgent Runbook"
        case (.ja, .preflightChecks): return "事前確認"
        case (.en, .preflightChecks): return "Preflight Checks"
        case (.ja, .verification): return "動作確認"
        case (.en, .verification): return "Verification"
        case (.ja, .securityBoundary): return "セキュリティ境界"
        case (.en, .securityBoundary): return "Security Boundary"
        case (.ja, .troubleshooting): return "トラブルシュート"
        case (.en, .troubleshooting): return "Troubleshooting"
        case (.ja, .close): return "閉じる"
        case (.en, .close): return "Close"
        case (.ja, .logPaths): return "ログパス"
        case (.en, .logPaths): return "Log Paths"
        case (.ja, .plistPreview): return "plist プレビュー"
        case (.en, .plistPreview): return "Plist Preview"
        case (.ja, .environmentAssumptions): return "環境前提"
        case (.en, .environmentAssumptions): return "Environment Assumptions"
        case (.ja, .programArguments): return "起動引数"
        case (.en, .programArguments): return "Program Arguments"
        case (.ja, .copyPlist): return "plistファイルをコピー"
        case (.en, .copyPlist): return "Copy Plist"
        case (.ja, .previewMetadata): return "プレビュー情報"
        case (.en, .previewMetadata): return "Preview Metadata"
        case (.ja, .operationId): return "操作ID"
        case (.en, .operationId): return "Operation ID"
        case (.ja, .previewHash): return "プレビューハッシュ"
        case (.en, .previewHash): return "Preview Hash"
        case (.ja, .previewApplyBoundary): return "プレビュー / 適用境界"
        case (.en, .previewApplyBoundary): return "Preview / Apply Boundary"
        case (.ja, .tailLogs): return "ログ追跡コマンド"
        case (.en, .tailLogs): return "Tail Commands"
        case (.ja, .launchctlPrint): return "launchctl print"
        case (.en, .launchctlPrint): return "launchctl print"
        case (.ja, .stdoutTail): return "stdout 追跡"
        case (.en, .stdoutTail): return "stdout tail"
        case (.ja, .stderrTail): return "stderr 追跡"
        case (.en, .stderrTail): return "stderr tail"
        case (.ja, .copyStdoutTail): return "stdout 追跡コマンドをコピー"
        case (.en, .copyStdoutTail): return "Copy stdout tail"
        case (.ja, .copyStderrTail): return "stderr 追跡コマンドをコピー"
        case (.en, .copyStderrTail): return "Copy stderr tail"
        case (.ja, .statusDiagnostics): return "状態診断"
        case (.en, .statusDiagnostics): return "Status Diagnostics"
        case (.ja, .proofDiagnostics): return "根拠診断"
        case (.en, .proofDiagnostics): return "Proof Diagnostics"
        case (.ja, .proofDiagnosticsSummary): return "identity / readiness / API readiness を根拠付きで確認する読み取りコマンドです"
        case (.en, .proofDiagnosticsSummary): return "Proof-oriented read commands for identity, readiness, and API readiness"
        case (.ja, .returnCode): return "リターンコード"
        case (.en, .returnCode): return "Return Code"
        case (.ja, .stderrPreview): return "stderr プレビュー"
        case (.en, .stderrPreview): return "stderr Preview"
        case (.ja, .needsAttention): return "要対応"
        case (.en, .needsAttention): return "Needs Attention"
        case (.ja, .verifyNow): return "確認ポイント"
        case (.en, .verifyNow): return "Verify Now"
        case (.ja, .healthySignals): return "正常シグナル"
        case (.en, .healthySignals): return "Healthy Signals"
        case (.ja, .suggestedAction): return "推奨アクション"
        case (.en, .suggestedAction): return "Suggested Action"
        case (.ja, .diagnosticPriority): return "復旧優先度"
        case (.en, .diagnosticPriority): return "Recovery Priority"
        case (.ja, .actionSummary): return "実行内容"
        case (.en, .actionSummary): return "Action Summary"
        case (.ja, .previousCandidate): return "前の候補"
        case (.en, .previousCandidate): return "Previous Candidate"
        case (.ja, .nextCandidate): return "次の候補"
        case (.en, .nextCandidate): return "Next Candidate"
        case (.ja, .queueActions): return "候補アクション"
        case (.en, .queueActions): return "Candidate Actions"
        case (.ja, .candidateResult): return "実行結果"
        case (.en, .candidateResult): return "Candidate Result"
        case (.ja, .resultForCurrentCandidate): return "この候補の最新結果"
        case (.en, .resultForCurrentCandidate): return "Latest result for this candidate"
        case (.ja, .targetSection): return "対象セクション"
        case (.en, .targetSection): return "Target Section"
        case (.ja, .inspectActions): return "確認"
        case (.en, .inspectActions): return "Inspect"
        case (.ja, .startActions): return "起動"
        case (.en, .startActions): return "Start"
        case (.ja, .recoverActions): return "復旧"
        case (.en, .recoverActions): return "Recover"
        case (.ja, .logActions): return "ログ確認"
        case (.en, .logActions): return "Logs"
        case (.ja, .commandDeck): return "操作デッキ"
        case (.en, .commandDeck): return "Command Deck"
        case (.ja, .searchCandidates): return "候補を絞り込む"
        case (.en, .searchCandidates): return "Search Candidates"
        case (.ja, .quickLinks): return "クイックリンク"
        case (.en, .quickLinks): return "Quick Links"
        case (.ja, .startHere): return "まずここから"
        case (.en, .startHere): return "Start Here"
        case (.ja, .noPriorityActions): return "今すぐ着手すべき項目はありません"
        case (.en, .noPriorityActions): return "There is nothing urgent to start right now"
        case (.ja, .noPriorityActionsDisconnected): return "最初にバックエンドを起動または再接続すると、この画面の優先項目を読み込めます"
        case (.en, .noPriorityActionsDisconnected): return "Start or reconnect the backend first to load the priority items for this screen"
        case (.ja, .reviewNextCandidate): return "次の候補を確認"
        case (.en, .reviewNextCandidate): return "Review Next Candidate"
        case (.ja, .reviewDaemonAction): return "バックエンドの次アクションを確認"
        case (.en, .reviewDaemonAction): return "Review Backend Action"
        case (.ja, .checkLaunchAgentStatus): return "LaunchAgentの状態を確認"
        case (.en, .checkLaunchAgentStatus): return "Check LaunchAgent Status"
        case (.ja, .openRunbook): return "運用手順書を開く"
        case (.en, .openRunbook): return "Open Runbook"
        case (.ja, .launchAgentFocus): return "LaunchAgent 注目点"
        case (.en, .launchAgentFocus): return "LaunchAgent Focus"
        case (.ja, .launchAgentFocusSummary): return "現在状態・復旧プレビュー・次コマンドをまとめて確認します"
        case (.en, .launchAgentFocusSummary): return "Review the current state, recovery previews, and next command first"
        case (.ja, .currentStateDetails): return "現在状態の詳細"
        case (.en, .currentStateDetails): return "Current State Details"
        case (.ja, .currentStateDetailsSummary): return "注目点の根拠をここで確認します"
        case (.en, .currentStateDetailsSummary): return "Use this section to verify the details behind the LaunchAgent Focus summary"
        case (.ja, .recoveryPreviewDetails): return "復旧プレビューの詳細"
        case (.en, .recoveryPreviewDetails): return "Recovery Preview Details"
        case (.ja, .recoveryPreviewDetailsSummary): return "復旧要約の内訳と注意点を確認します"
        case (.en, .recoveryPreviewDetailsSummary): return "Use this section to inspect the breakdown and cautions behind the focus recovery summary"
        case (.ja, .nextEpicWorkspace): return "次のエピック作業面"
        case (.en, .nextEpicWorkspace): return "Next Epic Workspace"
        case (.ja, .operatorSummaryRail): return "運用サマリーレール"
        case (.en, .operatorSummaryRail): return "Operator Summary Rail"
        case (.ja, .phaseClosureGates): return "フェーズ完了ゲート"
        case (.en, .phaseClosureGates): return "Phase Closure Gates"
        case (.ja, .openSection): return "セクションを開く"
        case (.en, .openSection): return "Open Section"
        case (.ja, .sectionNavigatorSummary): return "優先セクションへすぐ移動できます"
        case (.en, .sectionNavigatorSummary): return "Jump directly to the highest-priority sections"
        case (.ja, .prioritySections): return "優先セクション"
        case (.en, .prioritySections): return "Priority Sections"
        case (.ja, .otherSections): return "その他のセクション"
        case (.en, .otherSections): return "Other Sections"
        case (.ja, .nextEpicWorkspaceSummary): return "次の判断面とブロッカーをまとめて確認します"
        case (.en, .nextEpicWorkspaceSummary): return "Review the next decision surfaces and blockers together"
        case (.ja, .remainingWorkstreams): return "残りの判断面"
        case (.en, .remainingWorkstreams): return "Remaining Workstreams"
        case (.ja, .remainingWorkstreamsSummary): return "優先導線で触れていない判断面だけを残します"
        case (.en, .remainingWorkstreamsSummary): return "Keep only the workstreams not already covered by the priority path above"
        case (.ja, .priorityPathCoversCurrentWorkspace): return "現在の優先導線が主要な判断面をすでにカバーしています"
        case (.en, .priorityPathCoversCurrentWorkspace): return "The current priority path already covers the main decision surfaces"
        case (.ja, .phaseClosureGatesSummary): return "未完了ゲートと確認先を対応づけます"
        case (.en, .phaseClosureGatesSummary): return "Map unfinished gates to the surfaces that clarify them"
        case (.ja, .evidenceDrilldown): return "根拠ドリルダウン"
        case (.en, .evidenceDrilldown): return "Evidence Drill-down"
        case (.ja, .decisionAssist): return "判断支援"
        case (.en, .decisionAssist): return "Decision Assist"
        case (.ja, .operatorSummaryRailSummary): return "現在のゲート・次コマンド・次の確認先をまとめて見ます"
        case (.en, .operatorSummaryRailSummary): return "Keep the current gate, next command, and next read surface together first"
        case (.ja, .evidenceDrilldownSummary): return "関連する参照先を見比べて確認先を絞ります"
        case (.en, .evidenceDrilldownSummary): return "Compare related read surfaces to narrow the next check"
        case (.ja, .decisionAssistSummary): return "次の一手を要約とコマンドで示します"
        case (.en, .decisionAssistSummary): return "Show the next action first with a short summary and command"
        case (.ja, .statusSectionSummary): return "各運用面の状態・注目点・代表コマンドを確認します"
        case (.en, .statusSectionSummary): return "Review each operator surface through status, highlights, and commands"
        case (.ja, .operatorWorkspaceCompactSummary): return "重要な判断面を優先順とブロッカー付きで確認します"
        case (.en, .operatorWorkspaceCompactSummary): return "Review key decision surfaces with priority order and blockers"
        case (.ja, .currentGate): return "現在のゲート"
        case (.en, .currentGate): return "Current Gate"
        case (.ja, .nextReadSurface): return "次の確認先"
        case (.en, .nextReadSurface): return "Next Read Surface"
        case (.ja, .serviceControlAssistSummary): return "まずサービス制御境界を確認し、許可されたローカル制御を見極めます"
        case (.en, .serviceControlAssistSummary): return "Check the service control boundary first to confirm the allowed local control path"
        case (.ja, .recoveryAssistSummary): return "復旧フローと同意境界を確認します"
        case (.en, .recoveryAssistSummary): return "Review the recovery flow and consent boundary first"
        case (.ja, .supervisionAssistSummary): return "現在の監視モードと保留中の背景サーフェスを確認します"
        case (.en, .supervisionAssistSummary): return "Review the current supervision mode and deferred background surfaces"
        case (.ja, .inspectActionsSummary): return "現在の launchd 状態とバックエンドのヘルスを非破壊で確認します"
        case (.en, .inspectActionsSummary): return "Check the current launchd state and backend health without mutating anything"
        case (.ja, .recoverActionsSummary): return "cleanup / repair / bootout の順で古い状態を解消します"
        case (.en, .recoverActionsSummary): return "Clear stale state through cleanup, repair, and then bootout"
        case (.ja, .startActionsSummary): return "確認後に bootstrap / kickstart で起動します"
        case (.en, .startActionsSummary): return "Start with bootstrap or kickstart after the recovery checks"
        case (.ja, .logActionsSummary): return "ログの場所を確認してから tail で追跡します"
        case (.en, .logActionsSummary): return "Check the log locations first and then follow them with tail"
        case (.ja, .launchAgentAssistRuntimeInit): return "runtime-init プレビューを先に確認します"
        case (.en, .launchAgentAssistRuntimeInit): return "Review the runtime-init preview first"
        case (.ja, .launchAgentAssistHealthy): return "LaunchAgent の確認系コマンドから現在状態を再確認します"
        case (.en, .launchAgentAssistHealthy): return "Re-check the current LaunchAgent state from the inspection commands"
        case (.ja, .loadingState): return "読込中"
        case (.en, .loadingState): return "Loading"
        case (.ja, .screenOverview): return "表示中"
        case (.en, .screenOverview): return "Viewing"
        case (.ja, .bridgeConnected): return "バックエンド接続中"
        case (.en, .bridgeConnected): return "Backend Connected"
        case (.ja, .bridgeAttention): return "バックエンド要確認"
        case (.en, .bridgeAttention): return "Backend Needs Attention"
        case (.ja, .bridgeStatusPanel): return "バックエンド状態"
        case (.en, .bridgeStatusPanel): return "Backend Status"
        case (.ja, .bridgeReady): return "バックエンドは利用可能です"
        case (.en, .bridgeReady): return "Backend is available"
        case (.ja, .bridgeStarting): return "バックエンドは起動中です"
        case (.en, .bridgeStarting): return "Backend is starting"
        case (.ja, .bridgeNotConnected): return "バックエンドに未接続です"
        case (.en, .bridgeNotConnected): return "Backend is not connected"
        case (.ja, .bridgeStatusDetailDisconnected): return "バックエンドを起動すると各画面を読み込めます。macOS アプリから自動起動します"
        case (.en, .bridgeStatusDetailDisconnected): return "Start the backend to load the Home, Queue, and Backend State screens. The macOS app starts it automatically."
        case (.ja, .moreItems): return "ほか %d 件"
        case (.en, .moreItems): return "%d more"
        case (.ja, .bridgeVersion): return "バージョン"
        case (.en, .bridgeVersion): return "Version"
        case (.ja, .sourceUpdatedAt): return "ソース更新時刻"
        case (.en, .sourceUpdatedAt): return "Source Updated"
        case (.ja, .bridgeStatusPanelSummary): return "ここで接続状態を確認し、必要なら起動・再接続・ログ確認へ進みます。macOS アプリから自動起動します"
        case (.en, .bridgeStatusPanelSummary): return "Check connectivity here first, then start, reconnect, or inspect logs as needed. The macOS app starts it automatically."
        case (.ja, .connectionDiagnostics): return "接続診断"
        case (.en, .connectionDiagnostics): return "Connection Diagnostics"
        case (.ja, .debugShellCompatibilitySummary): return "通常操作ではなく、ブラウザでのデバッグ・互換確認・引き継ぎ用の経路です"
        case (.en, .debugShellCompatibilitySummary): return "Use this browser path only for debugging, compatibility checks, or handoff"
        case (.ja, .debugCompatibilityTools): return "デバッグ互換ツール"
        case (.en, .debugCompatibilityTools): return "Debug Compatibility Tools"
        case (.ja, .debugCompatibilityToolsSummary): return "通常の macOS 操作導線から外し、必要時だけ開くブラウザ互換経路です"
        case (.en, .debugCompatibilityToolsSummary): return "A browser compatibility path kept out of the normal macOS workflow until needed"
        case (.ja, .bridgeURL): return "バックエンド URL"
        case (.en, .bridgeURL): return "Backend URL"
        case (.ja, .healthEndpoint): return "ヘルスエンドポイント"
        case (.en, .healthEndpoint): return "Health Endpoint"
        case (.ja, .debugShell): return "ブラウザ互換シェル（デバッグ用）"
        case (.en, .debugShell): return "Browser Compatibility Shell (Debug)"
        case (.ja, .tokenFile): return "トークンファイル"
        case (.en, .tokenFile): return "Token File"
        case (.ja, .logFile): return "ログファイル"
        case (.en, .logFile): return "Log File"
        case (.ja, .profile): return "プロファイル"
        case (.en, .profile): return "Profile"
        case (.ja, .launchSource): return "起動ソース"
        case (.en, .launchSource): return "Launch Source"
        case (.ja, .lastLaunchFailure): return "直近の起動失敗"
        case (.en, .lastLaunchFailure): return "Last Launch Failure"
        case (.ja, .openToken): return "トークンを開く"
        case (.en, .openToken): return "Open Token"
        case (.ja, .openLaunchSource): return "起動ソースを開く"
        case (.en, .openLaunchSource): return "Open Launch Source"
        case (.ja, .openDebugShell): return "互換シェルを開く"
        case (.en, .openDebugShell): return "Open Compatibility Shell"
        case (.ja, .showDebugCompatibilityTools): return "デバッグ互換ツールを表示"
        case (.en, .showDebugCompatibilityTools): return "Show Debug Compatibility Tools"
        case (.ja, .hideDebugCompatibilityTools): return "デバッグ互換ツールを隠す"
        case (.en, .hideDebugCompatibilityTools): return "Hide Debug Compatibility Tools"
        case (.ja, .copyHealthCommand): return "ヘルス確認コマンドをコピー"
        case (.en, .copyHealthCommand): return "Copy Health Command"
        case (.ja, .copyLaunchSource): return "起動ソースをコピー"
        case (.en, .copyLaunchSource): return "Copy Launch Source"
        case (.ja, .copyStartupCommand): return "起動コマンドをコピー"
        case (.en, .copyStartupCommand): return "Copy Startup Command"
        case (.ja, .copyDebugShellURL): return "互換シェルURLをコピー"
        case (.en, .copyDebugShellURL): return "Copy Compatibility Shell URL"
        case (.ja, .openScreen): return "画面を開く"
        case (.en, .openScreen): return "Open Screen"
        case (.ja, .noQuickLinks): return "利用できるクイックリンクはありません"
        case (.en, .noQuickLinks): return "No quick links are available"
        case (.ja, .noReviewItems): return "レビュー候補はまだありません"
        case (.en, .noReviewItems): return "There are no review items yet"
        case (.ja, .noDaemonActions): return "バックエンドの次アクションはありません"
        case (.en, .noDaemonActions): return "There are no backend actions right now"
        case (.ja, .noCandidates): return "候補はまだありません"
        case (.en, .noCandidates): return "There are no candidates yet"
        case (.ja, .noCandidatesMatchingFilters): return "条件に一致する候補はありません"
        case (.en, .noCandidatesMatchingFilters): return "No candidates match the current filters"
        case (.ja, .selectCandidatePrompt): return "候補を選ぶと、詳細・差分・来歴を表示します"
        case (.en, .selectCandidatePrompt): return "Select a candidate to show its detail, diff, and lineage here"
        case (.ja, .detailUnavailable): return "候補詳細をまだ取得できていません"
        case (.en, .detailUnavailable): return "Candidate detail is not available yet"
        case (.ja, .loadingCandidates): return "候補と詳細を更新中です"
        case (.en, .loadingCandidates): return "Refreshing candidates and detail"
        case (.ja, .sectionNavigator): return "セクション移動"
        case (.en, .sectionNavigator): return "Section Navigator"
        case (.ja, .expandAll): return "すべて開く"
        case (.en, .expandAll): return "Expand All"
        case (.ja, .collapseAll): return "すべて閉じる"
        case (.en, .collapseAll): return "Collapse All"
        case (.ja, .noNextActions): return "次のアクションはありません"
        case (.en, .noNextActions): return "There are no next actions"
        case (.ja, .filteredCandidates): return "表示中の候補"
        case (.en, .filteredCandidates): return "Visible Candidates"
        case (.ja, .activeFilters): return "有効フィルタ"
        case (.en, .activeFilters): return "Active Filters"
        case (.ja, .noActiveFilters): return "フィルタなし"
        case (.en, .noActiveFilters): return "No Filters"
        case (.ja, .actionReadiness): return "実行できるアクション"
        case (.en, .actionReadiness): return "Available Actions"
        case (.ja, .shortcutLabel): return "ショートカット"
        case (.en, .shortcutLabel): return "Shortcut"
        case (.ja, .shortcutGuide): return "ショートカット"
        case (.en, .shortcutGuide): return "Shortcut Guide"
        case (.ja, .enabled): return "有効"
        case (.en, .enabled): return "Enabled"
        case (.ja, .disabled): return "無効"
        case (.en, .disabled): return "Disabled"
        case (.ja, .back): return "戻る"
        case (.en, .back): return "Back"
        case (.ja, .navigationTrail): return "移動履歴"
        case (.en, .navigationTrail): return "Navigation Trail"
        case (.ja, .allStatuses): return "全ステータス"
        case (.en, .allStatuses): return "All Statuses"
        case (.ja, .allSections): return "全セクション"
        case (.en, .allSections): return "All Sections"
        case (.ja, .filters): return "フィルタ"
        case (.en, .filters): return "Filters"
        case (.ja, .clearFilters): return "解除"
        case (.en, .clearFilters): return "Clear"
        case (.ja, .quickFilters): return "絞り込み候補"
        case (.en, .quickFilters): return "Quick Filters"
        case (.ja, .sortOrder): return "並び順"
        case (.en, .sortOrder): return "Sort Order"
        case (.ja, .sortNewest): return "新しい順"
        case (.en, .sortNewest): return "Newest First"
        case (.ja, .sortStatus): return "ステータス順"
        case (.en, .sortStatus): return "Status Order"
        case (.ja, .sortSection): return "セクション順"
        case (.en, .sortSection): return "Section Order"
        case (.ja, .diffSummary): return "差分の要約"
        case (.en, .diffSummary): return "Diff Summary"
        case (.ja, .addedItems): return "追加候補"
        case (.en, .addedItems): return "Added Items"
        case (.ja, .removedItems): return "削除候補"
        case (.en, .removedItems): return "Removed Items"
        case (.ja, .existingItems): return "既存項目"
        case (.en, .existingItems): return "Existing Items"
        case (.ja, .timelineEvent): return "イベント"
        case (.en, .timelineEvent): return "Timeline Event"
        case (.ja, .currentValue): return "現在"
        case (.en, .currentValue): return "Current"
        case (.ja, .mode): return "モード"
        case (.en, .mode): return "Mode"
        case (.ja, .consent): return "同意"
        case (.en, .consent): return "Consent"
        case (.ja, .recovery): return "復旧"
        case (.en, .recovery): return "Recovery"
        }
    }

    func summaryCardLabel(_ rawKey: String) -> String {
        switch (language, rawKey) {
        case (.ja, "repository"): return "リポジトリ"
        case (.en, "repository"): return "Repository"
        case (.ja, "reviewable"): return "レビュー対象"
        case (.en, "reviewable"): return "Reviewable"
        case (.ja, "approved_context"): return "承認済みコンテキスト"
        case (.en, "approved_context"): return "Approved Context"
        case (.ja, "blocked_context"): return "保留中コンテキスト"
        case (.en, "blocked_context"): return "Blocked Context"
        case (.ja, "daemon_state"): return "バックエンド状態"
        case (.en, "daemon_state"): return "Backend State"
        case (.ja, "next_actions"): return "次のアクション"
        case (.en, "next_actions"): return "Next Actions"
        case (.ja, "vault_status"): return "Vault状態"
        case (.en, "vault_status"): return "Vault Status"
        case (.ja, "vault_backend"): return "Vault バックエンド"
        case (.en, "vault_backend"): return "Vault Backend"
        case (.ja, "vault_assurance"): return "鍵保護"
        case (.en, "vault_assurance"): return "Key Assurance"
        case (.ja, "vault_session_count"): return "有効セッション数"
        case (.en, "vault_session_count"): return "Active Session Count"
        case (.ja, "packaging_model_decision"): return "パッケージング判断"
        case (.en, "packaging_model_decision"): return "Packaging Decision"
        case (.ja, "service_integration_line"): return "サービス統合"
        case (.en, "service_integration_line"): return "Service Integration"
        case (.ja, "supervision_ux_line"): return "監視体験判断"
        case (.en, "supervision_ux_line"): return "Supervision UX Decision"
        case (.ja, "recovery_and_consent_line"): return "復旧と同意"
        case (.en, "recovery_and_consent_line"): return "Recovery and Consent"
        case (.ja, "supervision_ux_decision"): return "監視体験判断"
        case (.en, "supervision_ux_decision"): return "Supervision UX Decision"
        case (.ja, "service_control_boundary_definition"): return "サービス制御境界"
        case (.en, "service_control_boundary_definition"): return "Service Control Boundary"
        case (.ja, "consent_and_recovery_alignment"): return "同意と復旧の整合"
        case (.en, "consent_and_recovery_alignment"): return "Consent and Recovery Alignment"
        case (.ja, "operator_handoff_update"): return "運用ハンドオフ更新"
        case (.en, "operator_handoff_update"): return "Operator Handoff Update"
        case (.ja, "supported_packaging_model_finalized"): return "サポートするパッケージング判断"
        case (.en, "supported_packaging_model_finalized"): return "Supported Packaging Model Finalized"
        case (.ja, "service_lifecycle_implementation_closed"): return "サービスライフサイクル実装"
        case (.en, "service_lifecycle_implementation_closed"): return "Service Lifecycle Implementation Closed"
        case (.ja, "platform_policy_and_rollback_closed"): return "プラットフォーム方針とロールバック"
        case (.en, "platform_policy_and_rollback_closed"): return "Platform Policy and Rollback Closed"
        case (.ja, "background_supervision_direction_decided"): return "背景監視方針"
        case (.en, "background_supervision_direction_decided"): return "Background Supervision Direction Decided"
        case (.ja, "recovery_and_consent_path_remains_explicit_under_next_model"): return "次モデルでも復旧と同意を明示"
        case (.en, "recovery_and_consent_path_remains_explicit_under_next_model"): return "Recovery and Consent Stay Explicit Under Next Model"
        case (.ja, "state"): return "状態"
        case (.en, "state"): return "State"
        case (.ja, "is_running_daemon"): return "バックエンド稼働"
        case (.en, "is_running_daemon"): return "Backend Running"
        case (.ja, "runtime_initialized"): return "ランタイム初期化"
        case (.en, "runtime_initialized"): return "Runtime Initialized"
        case (.ja, "readiness_status"): return "準備状況"
        case (.en, "readiness_status"): return "Readiness"
        default:
            return rawKey
                .split(separator: "_")
                .map { $0.capitalized }
                .joined(separator: " ")
        }
    }

    func fieldLabel(_ rawKey: String) -> String {
        switch (language, rawKey) {
        case (.ja, "status"): return "状態"
        case (.en, "status"): return "Status"
        case (.ja, "section"): return "セクション"
        case (.en, "section"): return "Section"
        case (.ja, "operation"): return "操作"
        case (.en, "operation"): return "Operation"
        case (.ja, "rde"): return "RDE"
        case (.en, "rde"): return "RDE"
        case (.ja, "phase"): return "フェーズ"
        case (.en, "phase"): return "Phase"
        case (.ja, "readiness"): return "準備状況"
        case (.en, "readiness"): return "Readiness"
        case (.ja, "flow"): return "フロー"
        case (.en, "flow"): return "Flow"
        case (.ja, "source_type"): return "ソース種別"
        case (.en, "source_type"): return "Source Type"
        case (.ja, "recommended_section"): return "推奨セクション"
        case (.en, "recommended_section"): return "Recommended Section"
        case (.ja, "review_surface"): return "レビュー面"
        case (.en, "review_surface"): return "Review Surface"
        case (.ja, "profile_update_recommended"): return "プロファイル更新推奨"
        case (.en, "profile_update_recommended"): return "Profile Update Recommended"
        case (.ja, "has_duplicates"): return "重複あり"
        case (.en, "has_duplicates"): return "Has Duplicates"
        case (.ja, "already_present"): return "既存項目"
        case (.en, "already_present"): return "Already Present"
        case (.ja, "add"): return "追加"
        case (.en, "add"): return "Add"
        case (.ja, "remove"): return "削除"
        case (.en, "remove"): return "Remove"
        case (.ja, "proposal_section"): return "提案セクション"
        case (.en, "proposal_section"): return "Proposal Section"
        case (.ja, "summary"): return "要約"
        case (.en, "summary"): return "Summary"
        case (.ja, "items"): return "項目"
        case (.en, "items"): return "Items"
        case (.ja, "parse_error"): return "解析エラー"
        case (.en, "parse_error"): return "Parse Error"
        case (.ja, "captured_at"): return "取り込み日時"
        case (.en, "captured_at"): return "Captured At"
        case (.ja, "current"): return "現在"
        case (.en, "current"): return "Current"
        case (.ja, "mode"): return "モード"
        case (.en, "mode"): return "Mode"
        case (.ja, "backend"): return "バックエンド"
        case (.en, "backend"): return "Backend"
        case (.ja, "consent"): return "同意"
        case (.en, "consent"): return "Consent"
        case (.ja, "recovery"): return "復旧"
        case (.en, "recovery"): return "Recovery"
        case (.ja, "label"): return "ラベル"
        case (.en, "label"): return "Label"
        case (.ja, "loaded"): return "読み込み"
        case (.en, "loaded"): return "Loaded"
        case (.ja, "plist_exists"): return "plist 存在"
        case (.en, "plist_exists"): return "Plist Exists"
        case (.ja, "stdout"): return "stdout"
        case (.en, "stdout"): return "stdout"
        case (.ja, "stderr"): return "stderr"
        case (.en, "stderr"): return "stderr"
        default:
            return summaryCardLabel(rawKey)
        }
    }

    func operatorReasonLabel(_ rawValue: String) -> String {
        switch (language, rawValue) {
        case (.ja, "Confirm phase closure blockers."): return "フェーズ完了を妨げるブロッカーを確認します。"
        case (.en, "Confirm phase closure blockers."): return "Confirm phase closure blockers."
        default: return rawValue
        }
    }

    func phaseChecklistItemLabel(_ rawValue: String) -> String {
        switch (language, rawValue) {
        case (.ja, "Packaging decision documented"): return "パッケージング判断が文書化されている"
        case (.en, "Packaging decision documented"): return "Packaging decision documented"
        default: return rawValue
        }
    }

    func booleanValueLabel(_ value: Bool) -> String {
        switch language {
        case .ja: return value ? "はい" : "いいえ"
        case .en: return value ? "Yes" : "No"
        }
    }

    func operatorPanelLabel(_ rawKey: String) -> String {
        switch (language, rawKey) {
        case (.ja, "packaging_status"): return "パッケージング状態"
        case (.en, "packaging_status"): return "Packaging Status"
        case (.ja, "service_targets"): return "サービス対象"
        case (.en, "service_targets"): return "Service Targets"
        case (.ja, "supervision_status"): return "監視状態"
        case (.en, "supervision_status"): return "Supervision Status"
        case (.ja, "recovery_consent_status"): return "復旧同意状態"
        case (.en, "recovery_consent_status"): return "Recovery Consent Status"
        case (.ja, "operator_phase_status"): return "運用フェーズ状態"
        case (.en, "operator_phase_status"): return "Operator Phase Status"
        default:
            return summaryCardLabel(rawKey)
        }
    }

    func operatorPanelPriority(_ rawKey: String) -> Int {
        switch rawKey {
        case "packaging_status": return 0
        case "service_targets": return 1
        case "recovery_consent_status": return 2
        case "supervision_status": return 3
        case "operator_phase_status": return 4
        default: return 99
        }
    }

    func highlightPriority(_ rawValue: String) -> Int {
        switch rawValue {
        case "separate_plan_required", "not_supported", "blocked", "missing": return 0
        case "review_required", "in_progress", "candidate_requires_phase_closure", "not_ready_for_phase_closure", "limited_cli_only", "manual": return 1
        case "available", "loaded", "running", "ready", "supported_preview_apply_control", "baseline_ready", "baseline_contract_implemented": return 2
        default: return 9
        }
    }

    func tokenLabel(_ rawValue: String) -> String {
        switch (language, rawValue) {
        case (.ja, "knowledge.concepts"): return "知識 / 概念"
        case (.en, "knowledge.concepts"): return "knowledge / concepts"
        case (.ja, "knowledge.preferences"): return "知識 / 嗜好"
        case (.en, "knowledge.preferences"): return "knowledge / preferences"
        case (.ja, "clipboard"): return "クリップボード"
        case (.en, "clipboard"): return "Clipboard"
        case (.ja, "evaluate_first"): return "まず評価してから判断"
        case (.en, "evaluate_first"): return "Evaluate first before deciding"
        case (.ja, "ready_for_decision"): return "承認・修正・却下を判断可能"
        case (.en, "ready_for_decision"): return "Ready for approve, revise, or reject"
        case (.ja, "revise_or_recheck"): return "再確認または修正を優先"
        case (.en, "revise_or_recheck"): return "Prefer re-checking or revising"
        case (.ja, "approved_complete"): return "承認済みで完了"
        case (.en, "approved_complete"): return "Already approved and complete"
        case (.ja, "rejected_closed"): return "却下済みでクローズ"
        case (.en, "rejected_closed"): return "Already rejected and closed"
        case (.ja, "review_state_check"): return "現在のレビュー状態を確認"
        case (.en, "review_state_check"): return "Check the current review state"
        case (.ja, "candidate_revision"): return "候補修正"
        case (.en, "candidate_revision"): return "Candidate Revision"
        case (.ja, "user_revision"): return "ユーザー修正"
        case (.en, "user_revision"): return "User Revision"
        case (.ja, "add"): return "追加"
        case (.en, "add"): return "Add"
        case (.ja, "remove"): return "削除"
        case (.en, "remove"): return "Remove"
        case (.ja, "revise"): return "修正"
        case (.en, "revise"): return "Revise"
        case (.ja, "Preserved"): return "保存された要素"
        case (.en, "Preserved"): return "Preserved"
        case (.ja, "running"): return "稼働中"
        case (.en, "running"): return "Running"
        case (.ja, "ready"): return "準備完了"
        case (.en, "ready"): return "Ready"
        case (.ja, "review_required"): return "レビュー要"
        case (.en, "review_required"): return "Review Required"
        case (.ja, "loaded"): return "読み込み済み"
        case (.en, "loaded"): return "Loaded"
        case (.ja, "manual"): return "手動"
        case (.en, "manual"): return "Manual"
        case (.ja, "in_progress"): return "進行中"
        case (.en, "in_progress"): return "In Progress"
        case (.ja, "not_ready_for_phase_closure"): return "フェーズ完了未準備"
        case (.en, "not_ready_for_phase_closure"): return "Not Ready For Phase Closure"
        case (.ja, "current_supported_line"): return "現在のサポート系統"
        case (.en, "current_supported_line"): return "Current Supported Line"
        case (.ja, "candidate_requires_phase_closure"): return "フェーズ完了後に判断"
        case (.en, "candidate_requires_phase_closure"): return "Candidate Requires Phase Closure"
        case (.ja, "candidate_requires_larger_architecture_change"): return "大きな設計変更が必要"
        case (.en, "candidate_requires_larger_architecture_change"): return "Requires Larger Architecture Change"
        case (.ja, "available"): return "利用可能"
        case (.en, "available"): return "Available"
        case (.ja, "supported_preview_apply_control"): return "プレビュー / 適用対応"
        case (.en, "supported_preview_apply_control"): return "Supported Preview/Apply Control"
        case (.ja, "separate_plan_required"): return "別計画が必要"
        case (.en, "separate_plan_required"): return "Separate Plan Required"
        case (.ja, "passive_local_observation_with_cli_recovery"): return "ローカル観測 + CLI復旧"
        case (.en, "passive_local_observation_with_cli_recovery"): return "Passive Local Observation With CLI Recovery"
        case (.ja, "explicit_cli_confirmation_for_mutation"): return "変更時はCLI明示確認"
        case (.en, "explicit_cli_confirmation_for_mutation"): return "Explicit CLI Confirmation For Mutation"
        case (.ja, "diagnose_then_operator_review_then_cli_action"): return "診断 → 確認 → CLI実行"
        case (.en, "diagnose_then_operator_review_then_cli_action"): return "Diagnose Then Operator Review Then CLI Action"
        case (.ja, "limited_cli_only"): return "CLI限定"
        case (.en, "limited_cli_only"): return "Limited CLI Only"
        case (.ja, "not_supported"): return "未対応"
        case (.en, "not_supported"): return "Not Supported"
        case (.ja, "cli_first_local_bridge"): return "CLI先行 + ローカルバックエンド"
        case (.en, "cli_first_local_bridge"): return "CLI First + Local Backend"
        case (.ja, "native_macos_app_primary"): return "macOS ネイティブアプリ"
        case (.en, "native_macos_app_primary"): return "Native macOS App"
        case (.ja, "local_bridge_shell_primary"): return "ローカルバックエンドシェル"
        case (.en, "local_bridge_shell_primary"): return "Local Backend Shell"
        case (.ja, "bridge_hosted_debug_shell"): return "バックエンド上の互換シェル"
        case (.en, "bridge_hosted_debug_shell"): return "Backend-hosted Compatibility Shell"
        case (.ja, "hybrid_local_bridge_plus_service_targets"): return "ローカルバックエンド + Service Target 併用候補"
        case (.en, "hybrid_local_bridge_plus_service_targets"): return "Hybrid Local Backend Plus Service Targets"
        case (.ja, "service_first_resident_runtime"): return "service-first 常駐ランタイム候補"
        case (.en, "service_first_resident_runtime"): return "Service-first Resident Runtime"
        case (.ja, "macos_launchagent"): return "macOS LaunchAgent"
        case (.en, "macos_launchagent"): return "macOS LaunchAgent"
        case (.ja, "post_app"): return "post-app"
        case (.en, "post_app"): return "post-app"
        case (.ja, "baseline_contract_implemented"): return "契約ベースライン実装済み"
        case (.en, "baseline_contract_implemented"): return "Baseline Contract Implemented"
        case (.ja, "baseline_contracts_implemented_next_phase_open"): return "ベースライン実装済み / 次フェーズ未完"
        case (.en, "baseline_contracts_implemented_next_phase_open"): return "Baseline Contracts Implemented / Next Phase Open"
        case (.ja, "blocked"): return "ブロック中"
        case (.en, "blocked"): return "Blocked"
        case (.ja, "baseline_ready"): return "ベースライン準備済み"
        case (.en, "baseline_ready"): return "Baseline Ready"
        case (.ja, "vault_unavailable"): return "Vault未接続"
        case (.en, "vault_unavailable"): return "Vault Unavailable"
        case (.ja, "unavailable"): return "未利用"
        case (.en, "unavailable"): return "Unavailable"
        case (.ja, "sqlite_test_local_vault"): return "SQLite テスト用 Local Vault"
        case (.en, "sqlite_test_local_vault"): return "SQLite Test Vault"
        case (.ja, "sqlite_development_local_vault"): return "SQLite 開発用 Local Vault"
        case (.en, "sqlite_development_local_vault"): return "SQLite Development Vault"
        case (.ja, "sqlite_macos_keychain_vault"): return "SQLite macOS keychain Vault"
        case (.en, "sqlite_macos_keychain_vault"): return "macOS Keychain Vault"
        case (.ja, "os_backed"): return "OS保護"
        case (.en, "os_backed"): return "OS Backed"
        case (.ja, "passphrase"): return "パスフレーズ"
        case (.en, "passphrase"): return "Passphrase"
        case (.ja, "test_only"): return "テスト限定"
        case (.en, "test_only"): return "Test Only"
        case (.ja, "deep_private"): return "厳重秘匿"
        case (.en, "deep_private"): return "Deep Private"
        case (.ja, "sensitive"): return "要保護"
        case (.en, "sensitive"): return "Sensitive"
        case (.ja, "normal"): return "通常"
        case (.en, "normal"): return "Normal"
        default:
            return rawValue
                .split(separator: "_")
                .map { $0.capitalized }
                .joined(separator: " ")
        }
    }

    func summaryValueLabel(key: String, value: String) -> String {
        switch key {
        case "state", "daemon_state", "readiness_status":
            return tokenLabel(value)
        case "is_running_daemon", "runtime_initialized":
            if value == "true" { return booleanValueLabel(true) }
            if value == "false" { return booleanValueLabel(false) }
            return tokenLabel(value)
        default:
            return tokenLabel(value)
        }
    }

    func residentValueLabel(_ value: String) -> String {
        tokenLabel(value)
    }

    func tone(forToken rawValue: String) -> StatusTone {
        switch rawValue {
        case "running", "loaded", "available", "approved", "evaluated", "captured", "supported_preview_apply_control", "os_backed":
            return .positive
        case "in_progress", "manual", "pending", "limited_cli_only", "candidate_requires_phase_closure", "not_ready_for_phase_closure", "passphrase":
            return .caution
        case "rejected", "not_supported", "separate_plan_required", "missing", "unavailable", "vault_unavailable":
            return .critical
        default:
            return .neutral
        }
    }

    func statusValueLabel(_ rawValue: String) -> String {
        switch (language, rawValue) {
        case (.ja, "pending"): return "保留"
        case (.en, "pending"): return "Pending"
        case (.ja, "evaluated"): return "評価済み"
        case (.en, "evaluated"): return "Evaluated"
        case (.ja, "approved"): return "承認済み"
        case (.en, "approved"): return "Approved"
        case (.ja, "rejected"): return "却下済み"
        case (.en, "rejected"): return "Rejected"
        case (.ja, "captured"): return "取り込み済み"
        case (.en, "captured"): return "Captured"
        case (.ja, "candidate_revised"): return "候補修正"
        case (.en, "candidate_revised"): return "Candidate Revised"
        case (.ja, "candidate_evaluated"): return "候補評価"
        case (.en, "candidate_evaluated"): return "Candidate Evaluated"
        case (.ja, "candidate_approved"): return "候補承認"
        case (.en, "candidate_approved"): return "Candidate Approved"
        case (.ja, "candidate_rejected"): return "候補却下"
        case (.en, "candidate_rejected"): return "Candidate Rejected"
        default:
            return rawValue
                .split(separator: "_")
                .map { $0.capitalized }
                .joined(separator: " ")
        }
    }

    func lineageDetailLabel(_ rawKey: String) -> String {
        switch (language, rawKey) {
        case (.ja, "candidate_id"): return "候補ID"
        case (.en, "candidate_id"): return "Candidate ID"
        case (.ja, "source_candidate_id"): return "元候補ID"
        case (.en, "source_candidate_id"): return "Source Candidate ID"
        case (.ja, "revised_candidate_id"): return "修正版候補ID"
        case (.en, "revised_candidate_id"): return "Revised Candidate ID"
        case (.ja, "decision"): return "判断"
        case (.en, "decision"): return "Decision"
        case (.ja, "event"): return "イベント"
        case (.en, "event"): return "Event"
        case (.ja, "context_path"): return "適用先"
        case (.en, "context_path"): return "Context Path"
        case (.ja, "created_at"): return "作成日時"
        case (.en, "created_at"): return "Created At"
        case (.ja, "captured_at"): return "取り込み日時"
        case (.en, "captured_at"): return "Captured At"
        case (.ja, "evaluated_at"): return "評価日時"
        case (.en, "evaluated_at"): return "Evaluated At"
        case (.ja, "approved_at"): return "承認日時"
        case (.en, "approved_at"): return "Approved At"
        case (.ja, "rejected_at"): return "却下日時"
        case (.en, "rejected_at"): return "Rejected At"
        case (.ja, "operation"): return "操作"
        case (.en, "operation"): return "Operation"
        case (.ja, "status"): return "状態"
        case (.en, "status"): return "Status"
        default:
            return summaryCardLabel(rawKey)
        }
    }

    func homeDaemonActionSummary(for action: String) -> String {
        if action.contains("status") || action.contains("health") {
            switch language {
            case .ja: return "現在のバックエンド / launchd 状態を先に確認します。"
            case .en: return "Check the current backend and launchd status first."
            }
        }
        if action.contains("start") || action.contains("bootstrap") || action.contains("kickstart") {
            switch language {
            case .ja: return "状態確認後に明示的に起動・再開します。"
            case .en: return "Start or resume explicitly after verifying status."
            }
        }
        if action.contains("repair") || action.contains("cleanup") || action.contains("bootout") {
            switch language {
            case .ja: return "不整合や旧状態を解消してから再実行します。"
            case .en: return "Clear stale state or inconsistencies before retrying."
            }
        }
        switch language {
        case .ja: return "ローカル CLI で次の手順を実行します。"
        case .en: return "Run the next step from the local CLI."
        }
    }

    func tone(forCommand command: String) -> StatusTone {
        if command.contains("repair") || command.contains("cleanup") || command.contains("bootout") {
            return .critical
        }
        if command.contains("start") || command.contains("bootstrap") || command.contains("kickstart") {
            return .caution
        }
        if command.contains("status") || command.contains("health") || command.contains("print") {
            return .positive
        }
        return .neutral
    }

    func commandPriorityTitle(for command: String) -> String {
        switch tone(forCommand: command) {
        case .critical:
            return text(.needsAttention)
        case .caution:
            return text(.suggestedAction)
        case .positive:
            return text(.verifyNow)
        case .neutral:
            return text(.actionSummary)
        }
    }

    func runtimeInitSummary(reviewRequired: Bool, itemCount: Int) -> String {
        let state = reviewRequired ? tokenLabel("review_required") : tokenLabel("ready")
        return "\(state) (\(itemCount))"
    }

    func cleanupSummary(removeCount: Int, totalCount: Int) -> String {
        switch language {
        case .ja: return "削除候補=\(removeCount), 合計=\(totalCount)"
        case .en: return "remove=\(removeCount), total=\(totalCount)"
        }
    }

    func repairSummary(missingCount: Int, totalCount: Int) -> String {
        switch language {
        case .ja: return "missing=\(missingCount), 合計=\(totalCount)"
        case .en: return "missing=\(missingCount), total=\(totalCount)"
        }
    }

    func environmentAssumptionLabel(_ kind: String, value: String) -> String {
        switch (language, kind) {
        case (.ja, "plist_path"): return "plist パス: \(value)"
        case (.en, "plist_path"): return "Plist Path: \(value)"
        case (.ja, "runtime_root"): return "ランタイムルート: \(value)"
        case (.en, "runtime_root"): return "Runtime Root: \(value)"
        case (.ja, "service_manager"): return "サービス管理: \(value)"
        case (.en, "service_manager"): return "Service Manager: \(value)"
        case (.ja, "working_model"): return "運用モデル: \(value)"
        case (.en, "working_model"): return "Working Model: \(value)"
        default: return "\(kind): \(value)"
        }
    }

    func diagnosticMessage(_ kind: String, count: Int? = nil) -> String {
        switch (language, kind) {
        case (.ja, "runtime_review_required"): return "runtime 初期化項目のレビューが必要です。"
        case (.en, "runtime_review_required"): return "Runtime initialization items require review."
        case (.ja, "cleanup_remove_candidates"): return "cleanup preview に remove 候補が \(count ?? 0) 件あります。"
        case (.en, "cleanup_remove_candidates"): return "Cleanup preview has \(count ?? 0) remove candidates."
        case (.ja, "repair_missing_items"): return "repair preview に missing 項目が \(count ?? 0) 件あります。"
        case (.en, "repair_missing_items"): return "Repair preview has \(count ?? 0) missing items."
        case (.ja, "stderr_attention"): return "launchagent stderr に要確認メッセージがあります。"
        case (.en, "stderr_attention"): return "LaunchAgent stderr contains messages that need review."
        case (.ja, "launchagent_loaded"): return "LaunchAgent は読み込み済みです。"
        case (.en, "launchagent_loaded"): return "The LaunchAgent is loaded."
        case (.ja, "plist_exists"): return "plist は存在しています。"
        case (.en, "plist_exists"): return "The plist file exists."
        case (.ja, "cleanup_clear"): return "cleanup preview に削除推奨はありません。"
        case (.en, "cleanup_clear"): return "Cleanup preview has no removal recommendations."
        case (.ja, "repair_clear"): return "repair preview に missing 項目はありません。"
        case (.en, "repair_clear"): return "Repair preview has no missing items."
        case (.ja, "launchctl_print_available"): return "launchctl print で詳細確認できます。"
        case (.en, "launchctl_print_available"): return "Use launchctl print for deeper inspection."
        default: return kind
        }
    }

    func diagnosticSummaryLabel(_ kind: String) -> String {
        switch (language, kind) {
        case (.ja, "runtime_init"): return "ランタイム初期化"
        case (.en, "runtime_init"): return "Runtime Init"
        case (.ja, "cleanup_preview"): return "クリーンアップ確認"
        case (.en, "cleanup_preview"): return "Cleanup Preview"
        case (.ja, "repair_preview"): return "修復確認"
        case (.en, "repair_preview"): return "Repair Preview"
        default: return kind
        }
    }

    func troubleshootingNotes() -> [String] {
        switch language {
        case .ja:
            return [
                "Already bootstrapped の場合は bootout の後に bootstrap します",
                "ヘルスチェックが失敗したら stderr のログパスを確認します",
                "sayane command not found の場合は `which sayane` と plist のパスを再確認します",
                "ログが空なら kickstart -k を実行します",
                "ログイン後に落ちる場合は plist の KeepAlive=true を確認します",
            ]
        case .en:
            return [
                "If already bootstrapped, run bootout first and then bootstrap.",
                "If the health check fails, inspect the stderr log path.",
                "If sayane is not found, re-check which sayane and the plist path.",
                "If logs are empty, run kickstart -k.",
                "If it falls after login, confirm KeepAlive is true in the plist.",
            ]
        }
    }

    func securityBoundaryNotes() -> [String] {
        switch language {
        case .ja:
            return [
                "bind host は 127.0.0.1 のまま維持します",
                "LaunchAgent 経路では --allow-all-interfaces を使いません",
                "~/.sayane/bridge.token は 0600 を維持します",
            ]
        case .en:
            return [
                "Keep the bind host on 127.0.0.1.",
                "Do not use --allow-all-interfaces in the LaunchAgent path.",
                "~/.sayane/bridge.token must remain 0600.",
            ]
        }
    }

    func previewApplyBoundaryNotes() -> [String] {
        switch language {
        case .ja:
            return [
                "preview ではファイル変更やサービス読み込みを行いません",
                "plist の書き込みは、このネイティブ read-first 画面の外で明示的な apply 確認が必要です",
                "apply では 操作ID と プレビューハッシュ の一致が必要です",
                "service bootstrap は明示的な local launchctl 手順のまま維持します",
            ]
        case .en:
            return [
                "Preview does not mutate files or load the service.",
                "Plist writes require explicit apply confirmation outside this native read-first surface.",
                "Apply must match the operation id and preview hash.",
                "Service bootstrap remains an explicit local launchctl step.",
            ]
        }
    }

    func captureActionMessage(id: String) -> String {
        switch language {
        case .ja: return "取り込み完了: \(id)"
        case .en: return "Captured: \(id)"
        }
    }

    func vaultSessionOpenedMessage(level: String) -> String {
        switch language {
        case .ja: return "アンロックセッションを開始: \(tokenLabel(level))"
        case .en: return "Opened unlock session: \(tokenLabel(level))"
        }
    }

    func vaultSessionsLockedMessage() -> String {
        switch language {
        case .ja: return "アンロックセッションをロックしました"
        case .en: return "Locked Local Vault sessions"
        }
    }

    func evaluationLevelLabel(_ level: Int, detailed: Bool = false) -> String {
        switch (language, level, detailed) {
        case (.ja, 1, true): return "クイック確認（ヒューリスティックのみ）"
        case (.ja, 2, true): return "ローカルAI確認（クイック確認を含む）"
        case (.ja, 3, true): return "外部AI確認（ローカルAI確認とクイック確認を含む）"
        case (.en, 1, true): return "Quick check (heuristics only)"
        case (.en, 2, true): return "Local AI check (includes quick check)"
        case (.en, 3, true): return "External AI check (includes local and quick checks)"
        case (.ja, 1, false): return "クイック確認"
        case (.ja, 2, false): return "ローカルAI確認"
        case (.ja, 3, false): return "外部AI確認"
        case (.en, 1, false): return "Quick check"
        case (.en, 2, false): return "Local AI check"
        case (.en, 3, false): return "External AI check"
        default: return "\(level)"
        }
    }

    func evaluateActionMessage(id: String, level: Int) -> String {
        switch language {
        case .ja: return "評価完了: \(id)（\(evaluationLevelLabel(level))）"
        case .en: return "Evaluated: \(id) (\(evaluationLevelLabel(level)))"
        }
    }

    func approveActionMessage(id: String) -> String {
        switch language {
        case .ja: return "承認完了: \(id)"
        case .en: return "Approved: \(id)"
        }
    }

    func rejectActionMessage(id: String) -> String {
        switch language {
        case .ja: return "却下完了: \(id)"
        case .en: return "Rejected: \(id)"
        }
    }

    func reviseActionMessage(id: String, originalID: String) -> String {
        switch language {
        case .ja: return "修正版を作成: \(originalID) → \(id)"
        case .en: return "Created revised candidate: \(originalID) → \(id)"
        }
    }

    func bridgeActionInProgressMessage(startingBridge: Bool) -> String {
        switch (language, startingBridge) {
        case (.ja, true):
            return "バックエンドを起動しています。ローカル接続が応答するまで少し待ってから再接続します。"
        case (.en, true):
            return "Starting the backend. Wait briefly for the local endpoint to respond, then reconnect."
        case (.ja, false):
            return "バックエンドへ再接続しています。接続診断とログを確認しながら待機します。"
        case (.en, false):
            return "Reconnecting to the backend. Wait while checking the diagnostics and logs if needed."
        }
    }

    func bridgeLaunchWarmupMessage() -> String {
        switch language {
        case .ja:
            return "バックエンドを起動しました。ローカル接続が応答するまで少し待ってから再接続します。"
        case .en:
            return "The backend has started. Wait briefly for the local endpoint to respond, then reconnect."
        }
    }

    func bridgeStartupSummary() -> String {
        switch language {
        case .ja:
            return "起動または再接続してから各画面を読み込みます。"
        case .en:
            return "Start or reconnect first, then load the Home, Queue, and Backend State screens."
        }
    }

    func bridgeTerminalRetentionSummary() -> String {
        switch language {
        case .ja:
            return "macOS アプリから自動起動します。"
        case .en:
            return "The macOS app starts it automatically."
        }
    }

    func bridgeStatusDetailText(
        status: String?,
        version: String?,
        sourceUpdatedAt: String?
    ) -> String {
        let normalizedStatus = status?.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        switch (language, normalizedStatus) {
        case (.ja, nil):
            return "バックエンドを起動すると \(bridgeStartupSummary()) \(bridgeTerminalRetentionSummary())"
        case (.en, nil):
            return "Start the backend to \(Self.lowercasedFirstLetter(bridgeStartupSummary())) \(bridgeTerminalRetentionSummary())"
        case (.ja, "starting"), (.ja, "bootstrapping"):
            let versionLabel = version ?? "-"
            return "バックエンドは起動中です。\(bridgeTerminalRetentionSummary()) バージョン: \(versionLabel)"
        case (.en, "starting"), (.en, "bootstrapping"):
            let versionLabel = version ?? "-"
            return "The backend is starting. \(bridgeTerminalRetentionSummary()) Version: \(versionLabel)"
        default:
            let versionLabel = version ?? "-"
            if let sourceUpdatedAt, !sourceUpdatedAt.isEmpty {
                return "\(text(.bridgeVersion)): \(versionLabel) · \(text(.sourceUpdatedAt)): \(sourceUpdatedAt)"
            }
            return "\(text(.bridgeVersion)): \(versionLabel)"
        }
    }

    func bridgeStatusPanelSummaryText(status: String?) -> String {
        let normalizedStatus = status?.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        switch (language, normalizedStatus) {
        case (.ja, nil):
            return "まずここから \(bridgeStartupSummary()) \(bridgeTerminalRetentionSummary())"
        case (.en, nil):
            return "Start or reconnect the backend here first, then load the Home, Queue, and Backend State screens. \(bridgeTerminalRetentionSummary())"
        case (.ja, "starting"), (.ja, "bootstrapping"):
            return "バックエンドは起動中です。まずローカル応答を待ち、必要なら再接続またはログ確認へ進みます。\(bridgeTerminalRetentionSummary())"
        case (.en, "starting"), (.en, "bootstrapping"):
            return "The backend is starting. Wait for the local endpoint first, then reconnect or inspect logs if needed. \(bridgeTerminalRetentionSummary())"
        default:
            return "ここで接続状態を確認し、必要なら起動・再接続・ログ確認へ進みます。\(bridgeTerminalRetentionSummary())"
        }
    }

    func bridgeRecoveryFailureMessage(_ detail: String) -> String {
        switch language {
        case .ja:
            return "\(detail)\n次は ~/.sayane/run-app-local.log を確認してください。"
        case .en:
            return "\(detail)\nNext, inspect ~/.sayane/run-app-local.log."
        }
    }

    func localizedBridgeErrorMessage(_ rawValue: String) -> String {
        let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty else { return value }
        switch language {
        case .ja:
            if let path = Self.removingPrefix("Missing bearer token at ", from: value) {
                return "Bearer トークンが見つかりません: \(path)"
            }
            if value == "Invalid Bridge response" {
                return "バックエンドからの応答を解釈できません。"
            }
            if let detail = Self.removingPrefix("HTTP ", from: value), let separator = detail.firstIndex(of: ":") {
                let status = String(detail[..<separator]).trimmingCharacters(in: .whitespaces)
                let body = String(detail[detail.index(after: separator)...]).trimmingCharacters(in: .whitespaces)
                return "バックエンドから HTTP \(status) が返りました: \(localizedBridgeErrorDetail(body))"
            }
            if value == "Could not connect to local Bridge" {
                return "ローカルバックエンドに接続できません。"
            }
            if value == "Could not locate the Sayane repository root from the current working directory." {
                return "現在の作業ディレクトリから Sayane リポジトリを見つけられません。"
            }
            if let path = Self.removingPrefix("Missing launcher script: ", from: value) {
                return "バックエンドの起動スクリプトが見つかりません: \(path)"
            }
            if let path = Self.removingPrefix("Missing backend launcher script: ", from: value) {
                return "バックエンドの起動スクリプトが見つかりません: \(path)"
            }
            if let message = Self.removingPrefix("Bridge launch failed: ", from: value) {
                let cleaned = message
                    .replacingOccurrences(of: "\nCheck the opened Bridge Terminal window or ~/.sayane/run-app-local.log.", with: "")
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                return "バックエンドの起動に失敗しました: \(localizedBridgeErrorDetail(cleaned))"
            }
            if let message = Self.removingPrefix("Backend launch failed: ", from: value) {
                let cleaned = message
                    .replacingOccurrences(of: "\nCheck ~/.sayane/run-app-local.log.", with: "")
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                return "バックエンドの起動に失敗しました: \(localizedBridgeErrorDetail(cleaned))"
            }
            return localizedBridgeErrorDetail(value)
        case .en:
            return value
        }
    }

    private func localizedBridgeErrorDetail(_ rawValue: String) -> String {
        switch language {
        case .ja:
            return rawValue
                .replacingOccurrences(of: "Missing or invalid resident app UI session", with: "Resident App の UI セッションが見つからないか無効です")
                .replacingOccurrences(of: "Missing or invalid resident app UI セッション", with: "Resident App の UI セッションが見つからないか無効です")
                .replacingOccurrences(of: "Missing or invalid UI session", with: "UI セッションが見つからないか無効です")
                .replacingOccurrences(of: "Missing or invalid UI セッション", with: "UI セッションが見つからないか無効です")
                .replacingOccurrences(of: "Missing bootstrap bearer or valid resident app UI session", with: "bootstrap bearer または有効な Resident App UI セッションがありません")
                .replacingOccurrences(of: "Missing bootstrap bearer or valid resident app UI セッション", with: "bootstrap bearer または有効な Resident App UI セッションがありません")
                .replacingOccurrences(of: "Unknown error", with: "不明なエラー")
                .replacingOccurrences(of: "connection refused", with: "接続が拒否されました")
                .replacingOccurrences(of: "Connection refused", with: "接続が拒否されました")
                .replacingOccurrences(of: "failed to connect", with: "接続に失敗しました")
                .replacingOccurrences(of: "Failed to connect", with: "接続に失敗しました")
                .replacingOccurrences(of: "missing bootstrap bearer", with: "bootstrap bearer がありません")
                .replacingOccurrences(of: "missing bearer token", with: "bearer トークンが見つかりません")
        case .en:
            return rawValue
        }
    }

    func bridgeRecoveryHintTitle(issue: String) -> String {
        switch (language, issue) {
        case (.ja, "missing_token"):
            return "バックエンドトークンを確認"
        case (.en, "missing_token"):
            return "Check the backend token"
        case (.ja, "ui_session"):
            return "バックエンドセッションを作り直す"
        case (.en, "ui_session"):
            return "Recreate the backend session"
        case (.ja, "not_connected"):
            return "バックエンドを先に起動"
        case (.en, "not_connected"):
            return "Start the backend first"
        default:
            return text(.connectionDiagnostics)
        }
    }

    func bridgeRecoveryIssueTitle(issue: String) -> String {
        switch (language, issue) {
        case (.ja, "missing_token"):
            return "バックエンドトークンが見つかりません"
        case (.en, "missing_token"):
            return "The backend token is missing"
        case (.ja, "ui_session"):
            return "バックエンドセッションが無効です"
        case (.en, "ui_session"):
            return "The backend session is invalid"
        case (.ja, "not_connected"):
            return "バックエンドがまだ起動していません"
        case (.en, "not_connected"):
            return "The backend is not running yet"
        default:
            return text(.connectionProblem)
        }
    }

    func bridgeRecoveryIssueSummary(issue: String) -> String {
        switch (language, issue) {
        case (.ja, "missing_token"):
            return "認証用トークンを読めないため、このアプリからバックエンド API を呼び出せません。"
        case (.en, "missing_token"):
            return "This app cannot call the backend API because it cannot read the authentication token."
        case (.ja, "ui_session"):
            return "バックエンドには到達していますが、Resident App の UI セッションが切れているため再接続が必要です。"
        case (.en, "ui_session"):
            return "The app can reach the backend, but the Resident App UI session has expired and must be refreshed."
        case (.ja, "not_connected"):
            return "バックエンドの待受がまだ無いため、\(bridgeStartupSummary())"
        case (.en, "not_connected"):
            return "Home, Queue, and Backend State cannot load because the backend is not listening yet."
        default:
            return text(.sessionProblem)
        }
    }

    func bridgeRecoveryStepMessages(issue: String, startupAvailable: Bool) -> [String] {
        switch (language, issue) {
        case (.ja, "missing_token"):
            var steps = ["トークンファイルが読めるか確認します。"]
            if startupAvailable {
                steps.append("ランチャーからバックエンドを起動し直してトークンを再生成します。")
            }
            steps.append("解決しない場合はログを開いて失敗理由を確認します。")
            return steps
        case (.en, "missing_token"):
            var steps = ["Check whether the token file can be read."]
            if startupAvailable {
                steps.append("Restart the backend from the launcher to regenerate the token.")
            }
            steps.append("If it still fails, open the logs and inspect the launch error.")
            return steps
        case (.ja, "ui_session"):
            var steps = ["まず再接続を実行して UI セッションを更新します。"]
            if startupAvailable {
                steps.append("直らなければランチャーからバックエンドを再起動します。")
            }
            steps.append("その後にもう一度この画面で再接続します。")
            return steps
        case (.en, "ui_session"):
            var steps = ["Reconnect first to refresh the UI session."]
            if startupAvailable {
                steps.append("If that does not fix it, restart the backend from the launcher.")
            }
            steps.append("Then reconnect again from this screen.")
            return steps
        case (.ja, "not_connected"):
            var steps = ["バックエンドがまだ待受していません。"]
            if startupAvailable {
                steps.append("ランチャーからバックエンドを起動します。")
            }
            steps.append("起動後にこの画面で再接続または更新します。")
            return steps
        case (.en, "not_connected"):
            var steps = ["The backend is not listening yet."]
            if startupAvailable {
                steps.append("Start the backend from the launcher.")
            }
            steps.append("After it starts, reconnect or refresh from this screen.")
            return steps
        default:
            var steps = ["Run the recovery action from this screen first."]
            if startupAvailable {
                steps.append("If needed, relaunch the backend from the launcher.")
            }
            steps.append("Use diagnostics and logs to inspect the next failure detail.")
            return steps
        }
    }

    func savedFileMessage(path: String) -> String {
        switch language {
        case .ja: return "ファイル保存: \(path)"
        case .en: return "Saved file: \(path)"
        }
    }

    func copiedCommandMessage(context: String? = nil) -> String {
        guard let context, !context.isEmpty else {
            return text(.copiedCommand)
        }
        return "\(text(.copiedCommand)): \(context)"
    }

    func moreItemsMessage(_ count: Int) -> String {
        switch language {
        case .ja: return String(format: text(.moreItems), count)
        case .en: return String(format: text(.moreItems), count)
        }
    }

    func quickLinkLabel(screen: String) -> String {
        switch (language, screen) {
        case (.ja, "candidate_queue"): return "候補キューを開く"
        case (.en, "candidate_queue"): return "Open Candidate Queue"
        case (.ja, "daemon_panel"): return "バックエンド状態を開く"
        case (.en, "daemon_panel"): return "Open Backend State"
        default:
            return "\(text(.openScreen)): \(tokenLabel(screen))"
        }
    }

    enum Key {
        case appTitle, home, queue, daemon, refresh, refreshInProgress, retry, bootstrap, bootstrapInProgress, captureClipboard, openLogs, startBridge, startBridgeInProgress
        case status, nextActions, summaryCards, topReviewItems, topDaemonActions, reviewableCount
        case localVault, vaultPath, vaultSessions, activeSessions, sessionPurpose, expiresAt, idleExpiresAt, unlockNormal, unlockSensitive, unlockDeepPrivate, lockAll, unlockPolicies, recommendedSetup, supported, notSupported, vaultUnavailable, backend
        case statusCounts, topSections, detail, actionAvailability, proposal, evaluation, capturedText, diff, lineage, evaluate, approve, reject, revise
        case operatorPhase, serviceTargets, launchAgent, clipboardEmpty, connectionProblem
        case sessionProblem, loading, none, error, bridgeHealthy, bridgeStartupFocus, bridgeDisconnectedShort, screenSummaryPending, homeStartupSummary, currentCandidate, editedText
        case changeReason, rejectReason, evaluateLevel, submit, cancel, supportedPath
        case exitCriteria, notInScope, copyCommand, copyDetail, copyDiff, copyLineage, copyCurrentState, copyRecoveryPreview, copyOperatorSummary, copyPhaseGates, copyReadSurfaces, copySuggestedActions, exportHandoffNote, copiedCommand, actionCompleted, savedFile, actionFailed, openPlist, openRuntime, openLauncher
        case reviewPreviews, generatedAt, bridgeContext, component, currentState, reason, notes, scope, recommended, errorDetails, showErrorDetails, hideErrorDetails, currentPlatform, loadedStatus
        case packagingModels, primaryOperatorUI, recommendedLauncher, operatorSurfaceNotes, supervision, recoveryPolicy, backgroundSurfaces, guardrails
        case blockedBy, nextCommand, additionalBlockers, allowedCommands, deferredCommands, recoveryFlow, passiveVisibility
        case activeSupervision, startupVisibility, phaseChecklist, readSurfaces
        case localOnly, statusValue, startupCommand, bootstrapUI
        case handoffSnapshot, workstreams, platformScope, operatorValue, implementationOrder
        case serviceLifecycle, policyGates, governingRules, appUIPolicy, allowedReads
        case allowedWrites, allowedControlExposure, forbiddenExposure, platformTargets, rollbackRequired, policyRequired
        case launchAgentRunbook, preflightChecks, verification, securityBoundary, troubleshooting, close
        case logPaths, plistPreview, environmentAssumptions, programArguments, copyPlist
        case previewMetadata, operationId, previewHash
        case previewApplyBoundary, tailLogs, launchctlPrint, stdoutTail, stderrTail, copyStdoutTail, copyStderrTail
        case statusDiagnostics, proofDiagnostics, proofDiagnosticsSummary, returnCode, stderrPreview
        case needsAttention, verifyNow, healthySignals, suggestedAction, diagnosticPriority, actionSummary
        case previousCandidate, nextCandidate, queueActions, targetSection
        case candidateResult, resultForCurrentCandidate
        case inspectActions, startActions, recoverActions, logActions, commandDeck
        case searchCandidates, quickLinks, startHere, noPriorityActions, noPriorityActionsDisconnected, reviewNextCandidate, reviewDaemonAction
        case checkLaunchAgentStatus, openRunbook, launchAgentFocus, launchAgentFocusSummary
        case currentStateDetails, currentStateDetailsSummary, recoveryPreviewDetails, recoveryPreviewDetailsSummary
        case nextEpicWorkspace, operatorSummaryRail, phaseClosureGates, openSection, evidenceDrilldown, decisionAssist
        case operatorSummaryRailSummary, currentGate, nextReadSurface
        case sectionNavigatorSummary, prioritySections, otherSections, nextEpicWorkspaceSummary, remainingWorkstreams, remainingWorkstreamsSummary, priorityPathCoversCurrentWorkspace, phaseClosureGatesSummary
        case evidenceDrilldownSummary, decisionAssistSummary
        case statusSectionSummary, operatorWorkspaceCompactSummary, moreItems
        case serviceControlAssistSummary, recoveryAssistSummary, supervisionAssistSummary
        case inspectActionsSummary, recoverActionsSummary, startActionsSummary, logActionsSummary
        case launchAgentAssistRuntimeInit, launchAgentAssistHealthy
        case loadingState, screenOverview, bridgeConnected, bridgeAttention
        case bridgeStatusPanel, bridgeReady, bridgeStarting, bridgeNotConnected, bridgeStatusDetailDisconnected
        case bridgeVersion, sourceUpdatedAt, bridgeStatusPanelSummary
        case bridgeStartedMessage, bridgeReconnectedMessage, bridgeRefreshedMessage
        case connectionDiagnostics, bridgeURL, healthEndpoint, debugShellCompatibilitySummary, debugShell, tokenFile, logFile, profile, launchSource, lastLaunchFailure
        case debugCompatibilityTools, debugCompatibilityToolsSummary, openToken, openLaunchSource, openDebugShell, showDebugCompatibilityTools, hideDebugCompatibilityTools, copyHealthCommand, copyLaunchSource, copyStartupCommand, copyDebugShellURL, openScreen
        case noQuickLinks, noReviewItems, noDaemonActions, noCandidates, noCandidatesMatchingFilters
        case selectCandidatePrompt, detailUnavailable, loadingCandidates
        case sectionNavigator, expandAll, collapseAll, noNextActions
        case filteredCandidates, activeFilters, noActiveFilters, actionReadiness, shortcutLabel, shortcutGuide, enabled, disabled
        case back, navigationTrail
        case allStatuses, allSections, filters, clearFilters
        case quickFilters
        case sortOrder, sortNewest, sortStatus, sortSection
        case diffSummary, addedItems, removedItems, existingItems
        case timelineEvent, currentValue, mode, consent, recovery
    }
}
