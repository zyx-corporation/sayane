import AppKit
import Foundation
import SwiftUI

@MainActor
final class AppModel: ObservableObject {
    private enum BridgeRecoveryIssue: String {
        case missingToken = "missing_token"
        case uiSession = "ui_session"
        case notConnected = "not_connected"
        case diagnostics = "diagnostics"
    }

    enum Screen: Hashable {
        case home
        case queue
        case daemon
    }

    private struct NavigationState: Equatable {
        let screen: Screen
        let candidateID: String?
    }

    struct SidebarMetadata: Equatable {
        let title: String
        let summary: String
        let badgeText: String?
        let badgeTone: StatusTone
    }

    struct CandidateActionRecord: Equatable {
        let candidateIDs: [String]
        let title: String
        let message: String
        let tone: StatusTone
    }

    struct DiagnosticRow: Equatable, Identifiable {
        let label: String
        let value: String

        var id: String { label }
    }

    @Published var selectedScreen: Screen = .home
    @Published var selectedCandidateID: String?
    @Published var health: HealthResponse?
    @Published var contract: AppContract?
    @Published var homeState: HomeScreenState?
    @Published var queueState: CandidateQueueScreenState?
    @Published var detailState: CandidateDetailScreenState?
    @Published var diffState: CandidateDiffPayload?
    @Published var lineageState: CandidateLineagePayload?
    @Published var daemonState: DaemonPanelScreenState?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var actionMessage: String?
    @Published var actionTitle: String?
    @Published var actionTone: StatusTone = .positive
    @Published var actionShowsProgress = false
    @Published var lastCandidateAction: CandidateActionRecord?
    @Published var showingReviseSheet = false
    @Published var showingRejectSheet = false
    @Published var showingEvaluateSheet = false
    @Published var hasLoadedInitialData = false
    @Published var lastBridgeLaunchFailure: String?

    let strings = AppStrings.current
    let bridgeClient: BridgeClient
    private var backStack: [NavigationState] = []
    private var hasAttemptedAutomaticBridgeStart = false

    init(bridgeClient: BridgeClient = BridgeClient()) {
        self.bridgeClient = bridgeClient
    }

    func bootstrapAndLoad() async {
        isLoading = true
        errorMessage = nil
        do {
            async let health = bridgeClient.health()
            async let contract = bridgeClient.contract()
            async let home = bridgeClient.homeState()
            async let queue = bridgeClient.queueState()
            async let daemon = bridgeClient.daemonState()
            self.health = try await health
            self.contract = try await contract
            self.homeState = try await home
            self.queueState = try await queue
            self.daemonState = try await daemon
            if selectedCandidateID == nil {
                selectedCandidateID = self.queueState?.items.first?.id
            }
            if let candidateID = selectedCandidateID {
                try await loadCandidate(candidateID: candidateID)
            }
            hasLoadedInitialData = true
            hasAttemptedAutomaticBridgeStart = false
            lastBridgeLaunchFailure = nil
            errorMessage = nil
            if actionTitle == strings.text(.connectionProblem) {
                dismissActionFeedback()
            }
        } catch {
            errorMessage = error.localizedDescription
            if !hasLoadedInitialData,
               bridgeRecoveryIssue == .notConnected,
               !hasAttemptedAutomaticBridgeStart,
               BridgeLauncher.canLaunchBridge()
            {
                hasAttemptedAutomaticBridgeStart = true
                await startBridgeAndReload()
                isLoading = false
                return
            }
            if !hasLoadedInitialData {
                showActionFeedback(
                    title: strings.text(.connectionProblem),
                    message: bridgeRecoveryIssueSummary,
                    tone: .caution
                )
            }
        }
        isLoading = false
    }

    func refreshCurrentScreen() async {
        switch selectedScreen {
        case .home:
            await loadHome()
        case .queue:
            await loadQueueAndDetail()
        case .daemon:
            await loadDaemon()
        }
    }

    func loadHome() async {
        isLoading = true
        defer { isLoading = false }
        do {
            async let health = bridgeClient.health()
            async let home = bridgeClient.homeState()
            self.health = try await health
            self.homeState = try await home
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func loadQueueAndDetail() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let queue = try await bridgeClient.queueState()
            self.queueState = queue
            if selectedCandidateID == nil || !(queue.items.contains { $0.id == selectedCandidateID }) {
                selectedCandidateID = queue.items.first?.id
            }
            if let candidateID = selectedCandidateID {
                try await loadCandidate(candidateID: candidateID)
            } else {
                detailState = nil
                diffState = nil
                lineageState = nil
            }
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func loadDaemon() async {
        isLoading = true
        defer { isLoading = false }
        do {
            self.daemonState = try await bridgeClient.daemonState()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func loadCandidate(candidateID: String) async throws {
        selectedCandidateID = candidateID
        async let detail = bridgeClient.detailState(candidateID: candidateID)
        async let diff = bridgeClient.diffState(candidateID: candidateID)
        async let lineage = bridgeClient.lineageState(candidateID: candidateID)
        self.detailState = try await detail
        self.diffState = try await diff
        self.lineageState = try await lineage
    }

    func choose(screen: Screen, recordHistory: Bool = true) {
        navigate(to: screen, candidateID: candidateIDForScreen(screen), recordHistory: recordHistory)
    }

    var currentScreenTitle: String {
        switch selectedScreen {
        case .home:
            strings.text(.home)
        case .queue:
            strings.text(.queue)
        case .daemon:
            strings.text(.daemon)
        }
    }

    var currentScreenSummary: String {
        sidebarMetadata(for: selectedScreen).summary
    }

    var shouldCondenseChromeMetadata: Bool {
        health == nil && !hasLoadedInitialData
    }

    var shouldShowNavigationTrailInStatusBar: Bool {
        !shouldCondenseChromeMetadata
    }

    var shouldShowSelectedCandidateInStatusBar: Bool {
        !shouldCondenseChromeMetadata
    }

    func sidebarMetadata(for screen: Screen) -> SidebarMetadata {
        if shouldCondenseChromeMetadata {
            return SidebarMetadata(
                title: screenTitle(for: screen),
                summary: strings.text(.screenSummaryPending),
                badgeText: screen == .home ? strings.text(.bridgeDisconnectedShort) : nil,
                badgeTone: .neutral
            )
        }
        switch screen {
        case .home:
            let reviewCount = homeState?.topReviewItems.count ?? 0
            return SidebarMetadata(
                title: strings.text(.home),
                summary: "\(strings.text(.topReviewItems)): \(reviewCount)",
                badgeText: reviewCount == 0 ? nil : String(reviewCount),
                badgeTone: reviewCount == 0 ? .neutral : .positive
            )
        case .queue:
            let reviewableCount = queueState?.reviewableCount ?? 0
            return SidebarMetadata(
                title: strings.text(.queue),
                summary: "\(strings.text(.reviewableCount)): \(reviewableCount)",
                badgeText: String(reviewableCount),
                badgeTone: reviewableCount == 0 ? .neutral : .caution
            )
        case .daemon:
            let phase = daemonState?.operatorPhaseSummary.phaseReadiness
                .map(strings.tokenLabel)
                ?? strings.text(.none)
            let tone = daemonState?.operatorPhaseSummary.phaseReadiness
                .map(strings.tone(forToken:))
                ?? .neutral
            return SidebarMetadata(
                title: strings.text(.daemon),
                summary: "\(strings.text(.operatorPhase)): \(phase)",
                badgeText: phase,
                badgeTone: tone
            )
        }
    }

    private func screenTitle(for screen: Screen) -> String {
        switch screen {
        case .home:
            strings.text(.home)
        case .queue:
            strings.text(.queue)
        case .daemon:
            strings.text(.daemon)
        }
    }

    var bridgeStatusText: String {
        guard let health else {
            return strings.text(.bridgeAttention)
        }
        if health.status == "ok" || health.status == "healthy" {
            return strings.text(.bridgeConnected)
        }
        return "\(strings.text(.bridgeAttention)): \(health.status)"
    }

    var bridgeStatusTone: StatusTone {
        guard let health else { return .critical }
        switch health.status {
        case "ok", "healthy":
            return .positive
        case "starting", "bootstrapping":
            return .caution
        default:
            return .critical
        }
    }

    var bridgeStatusHeadline: String {
        guard let health else {
            return strings.text(.bridgeNotConnected)
        }
        switch health.status {
        case "ok", "healthy":
            return strings.text(.bridgeReady)
        case "starting", "bootstrapping":
            return strings.text(.bridgeStarting)
        default:
            return "\(strings.text(.bridgeAttention)): \(health.status)"
        }
    }

    var bridgeStatusDetail: String {
        strings.bridgeStatusDetailText(
            status: health?.status,
            version: health?.version,
            sourceUpdatedAt: health?.sourceUpdatedAt
        )
    }

    var homeBridgeSummaryText: String {
        guard let health else {
            return strings.text(.homeStartupSummary)
        }
        let normalizedHeadline = bridgeStatusHeadline
            .replacingOccurrences(of: "\(strings.text(.bridgeAttention)): ", with: "")
            .replacingOccurrences(of: "Bridge は", with: "")
            .replacingOccurrences(of: "Bridge is ", with: "")
        return "\(strings.text(.bridgeHealthy)): \(normalizedHeadline) · \(health.version ?? "-")"
    }

    var homePriorityEmptyMessage: String {
        health == nil ? strings.text(.noPriorityActionsDisconnected) : strings.text(.noPriorityActions)
    }

    var homePriorityEmptyBadgeText: String {
        health == nil ? strings.text(.bridgeStartupFocus) : strings.text(.healthySignals)
    }

    var queueEmptyMessage: String {
        health == nil ? strings.text(.noPriorityActionsDisconnected) : strings.text(.noCandidates)
    }

    var queueEmptyBadgeText: String? {
        health == nil ? strings.text(.bridgeStartupFocus) : nil
    }

    var detailEmptyMessage: String {
        health == nil ? strings.text(.noPriorityActionsDisconnected) : strings.text(.selectCandidatePrompt)
    }

    var detailEmptyBadgeText: String {
        health == nil ? strings.text(.bridgeStartupFocus) : strings.text(.queue)
    }

    var daemonWorkspaceEmptyMessage: String {
        health == nil ? strings.text(.noPriorityActionsDisconnected) : strings.text(.noPriorityActions)
    }

    var daemonWorkspaceEmptyBadgeText: String? {
        health == nil ? strings.text(.bridgeStartupFocus) : nil
    }

    var daemonSummaryEmptyMessage: String {
        health == nil ? strings.text(.noPriorityActionsDisconnected) : strings.text(.noPriorityActions)
    }

    var daemonSummaryEmptyBadgeText: String? {
        health == nil ? strings.text(.bridgeStartupFocus) : nil
    }

    var bridgeSuggestedActionText: String {
        if bridgeRecoveryActionDisabled {
            guard let health else {
                return strings.text(.startBridgeInProgress)
            }
            switch health.status {
            case "ok", "healthy":
                return strings.text(.refreshInProgress)
            default:
                return strings.text(.bootstrapInProgress)
            }
        }
        guard let health else {
            return strings.text(.startBridge)
        }
        switch health.status {
        case "ok", "healthy":
            return strings.text(.refresh)
        case "starting", "bootstrapping":
            return strings.text(.retry)
        default:
            return strings.text(.bootstrap)
        }
    }

    var bridgeRecoveryActionDisabled: Bool {
        isLoading
    }

    var bridgeRecoveryInProgress: Bool {
        isLoading
    }

    var toolbarRefreshText: String {
        bridgeRecoveryInProgress ? bridgeSuggestedActionText : strings.text(.refresh)
    }

    var bridgeStatusPanelSummaryText: String {
        strings.bridgeStatusPanelSummaryText(status: health?.status)
    }

    var bridgeBaseURLText: String {
        bridgeClient.configuration.baseURL.absoluteString
    }

    var bridgeHealthURLText: String {
        bridgeClient.configuration.healthURL.absoluteString
    }

    var bridgeDebugShellEntryURLText: String {
        bridgeClient.configuration.debugShellEntryURL(token: bridgeBootstrapToken).absoluteString
    }

    var startupCommandText: String? {
        let value = daemonState?.operatorPhaseDetails.currentSupportedOperatorPath.startupCommandText?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard let value, !value.isEmpty else { return nil }
        return value
    }

    var currentGateText: String? {
        let token = daemonState?.operatorPhaseSummary.blockingReasons.first?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard let token, !token.isEmpty else { return nil }
        return strings.tokenLabel(token)
    }

    var nextDaemonCommandText: String? {
        let value = daemonState?.nextActions.first?.command
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard let value, !value.isEmpty else { return nil }
        return value
    }

    var nextDaemonReasonText: String? {
        let value = daemonState?.nextActions.first?.reason
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard let value, !value.isEmpty else { return nil }
        return strings.operatorReasonLabel(value)
    }

    var nextReadSurfaceText: String? {
        let value = daemonState?.operatorPhaseDetails.readSurfaces.first?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard let value, !value.isEmpty else { return nil }
        return value
    }

    var bridgeTokenFilePath: String {
        bridgeClient.configuration.tokenFileURL.path
    }

    var bridgeLogFilePath: String {
        bridgeClient.configuration.logFileURL.path
    }

    var bridgeLaunchSourceText: String {
        BridgeLauncher.launchDiagnosticSummary()
    }

    var bridgeProfileID: String {
        bridgeClient.configuration.profileID
    }

    var bridgeLaunchFailureText: String? {
        guard let lastBridgeLaunchFailure, !lastBridgeLaunchFailure.isEmpty else { return nil }
        return strings.localizedBridgeErrorMessage(lastBridgeLaunchFailure)
    }

    func bridgeDiagnosticRows(compact: Bool) -> [DiagnosticRow] {
        bridgePrimaryDiagnosticRows(compact: compact)
    }

    func bridgePrimaryDiagnosticRows(compact: Bool) -> [DiagnosticRow] {
        let essentialDisconnectedRows = [
            DiagnosticRow(label: strings.text(.healthEndpoint), value: bridgeHealthURLText),
            DiagnosticRow(label: strings.text(.launchSource), value: bridgeLaunchSourceText),
            DiagnosticRow(label: strings.text(.tokenFile), value: bridgeTokenFilePath),
            DiagnosticRow(label: strings.text(.logFile), value: bridgeLogFilePath),
        ]
        let essentialConnectedRows = [
            DiagnosticRow(label: strings.text(.bridgeURL), value: bridgeBaseURLText),
            DiagnosticRow(label: strings.text(.healthEndpoint), value: bridgeHealthURLText),
            DiagnosticRow(label: strings.text(.launchSource), value: bridgeLaunchSourceText),
            DiagnosticRow(label: strings.text(.profile), value: bridgeProfileID),
        ]

        let failureRows = bridgeLaunchFailureText.map {
            [DiagnosticRow(label: strings.text(.lastLaunchFailure), value: $0)]
        } ?? []

        let isDisconnectedOrStarting: Bool
        if let health {
            isDisconnectedOrStarting = ["starting", "bootstrapping"].contains(health.status.lowercased())
        } else {
            isDisconnectedOrStarting = true
        }

        if compact {
            return (isDisconnectedOrStarting ? essentialDisconnectedRows : essentialConnectedRows) + failureRows
        }

        let primaryRows = isDisconnectedOrStarting ? essentialDisconnectedRows : essentialConnectedRows
        let seen = Set(primaryRows.map(\.label))
        return primaryRows + failureRows.filter { !seen.contains($0.label) }
    }

    func bridgeDebugDiagnosticRows() -> [DiagnosticRow] {
        let rows = [
            DiagnosticRow(label: strings.text(.bridgeURL), value: bridgeBaseURLText),
            DiagnosticRow(label: strings.text(.bootstrapUI), value: bridgeDebugShellEntryURLText),
            DiagnosticRow(label: strings.text(.tokenFile), value: bridgeTokenFilePath),
            DiagnosticRow(label: strings.text(.logFile), value: bridgeLogFilePath),
            DiagnosticRow(label: strings.text(.profile), value: bridgeProfileID),
            DiagnosticRow(label: strings.text(.launchSource), value: bridgeLaunchSourceText),
        ]
        var seen = Set<String>()
        return rows.filter { seen.insert($0.label).inserted }
    }

    var hasDebugCompatibilitySurface: Bool {
        daemonState?.operatorPhaseDetails.currentSupportedOperatorPath.bootstrapUI != nil
    }

    var shouldPresentBlockingErrorView: Bool {
        errorMessage != nil && hasLoadedInitialData
    }

    var bridgeRecoveryHintTitle: String {
        strings.bridgeRecoveryHintTitle(issue: bridgeRecoveryIssue.rawValue)
    }

    var bridgeRecoveryIssueTitle: String {
        strings.bridgeRecoveryIssueTitle(issue: bridgeRecoveryIssue.rawValue)
    }

    var bridgeRecoveryIssueSummary: String {
        strings.bridgeRecoveryIssueSummary(issue: bridgeRecoveryIssue.rawValue)
    }

    var errorDisplayMessage: String? {
        guard let errorMessage, !errorMessage.isEmpty else { return nil }
        return strings.localizedBridgeErrorMessage(errorMessage)
    }

    var bridgeRecoveryStepMessages: [String] {
        strings.bridgeRecoveryStepMessages(
            issue: bridgeRecoveryIssue.rawValue,
            startupAvailable: startupCommandText != nil
        )
    }

    var bridgeRecoveryShowsTokenAction: Bool {
        switch bridgeRecoveryIssue {
        case .missingToken, .uiSession:
            return true
        default:
            return false
        }
    }

    var bridgeRecoveryShowsLauncherAction: Bool {
        guard let startupCommandText else { return false }
        return resolvedLocalCommandPath(startupCommandText) != nil
    }

    var bridgeRecoveryPrefersLauncherAction: Bool {
        bridgeRecoveryIssue == .notConnected && bridgeRecoveryShowsLauncherAction
    }

    var bridgeRecoveryPrefersTokenAction: Bool {
        bridgeRecoveryIssue == .missingToken && bridgeRecoveryShowsTokenAction
    }

    var bridgeNeedsExpandedRecoveryLayout: Bool {
        guard let health else { return true }
        return ["starting", "bootstrapping"].contains(health.status.lowercased())
            || bridgeRecoveryPrefersLauncherAction
            || bridgeRecoveryPrefersTokenAction
            || bridgeRecoveryShowsLauncherAction
            || bridgeRecoveryShowsTokenAction
    }

    private var bridgeBootstrapToken: String? {
        try? String(contentsOf: bridgeClient.configuration.tokenFileURL)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var bridgeRecoveryIssue: BridgeRecoveryIssue {
        let detail = (errorMessage ?? "").lowercased()
        if detail.contains("missing bearer token") || detail.contains("missing bootstrap bearer") {
            return .missingToken
        }
        if detail.contains("missing or invalid resident app ui session")
            || detail.contains("missing or invalid ui session")
            || detail.contains("http 401")
        {
            return .uiSession
        }
        if detail.contains("could not connect to local bridge")
            || detail.contains("connection refused")
            || detail.contains("failed to connect")
        {
            return .notConnected
        }
        return .diagnostics
    }

    var selectedCandidateBadgeText: String? {
        guard selectedScreen == .queue, let selectedCandidateID else {
            return nil
        }
        return "\(strings.text(.currentCandidate)): \(selectedCandidateID)"
    }

    var selectedCandidateActionRecord: CandidateActionRecord? {
        guard let selectedCandidateID else { return nil }
        guard let lastCandidateAction else { return nil }
        return lastCandidateAction.candidateIDs.contains(selectedCandidateID) ? lastCandidateAction : nil
    }

    var canGoBack: Bool {
        !backStack.isEmpty
    }

    var navigationTrailText: String {
        let root = strings.text(.home)
        switch selectedScreen {
        case .home:
            return root
        case .queue:
            if let selectedCandidateID {
                return "\(root) → \(strings.text(.queue)) → \(selectedCandidateID)"
            }
            return "\(root) → \(strings.text(.queue))"
        case .daemon:
            return "\(root) → \(strings.text(.daemon))"
        }
    }

    func goBack() {
        guard let previous = backStack.popLast() else { return }
        selectedScreen = previous.screen
        selectedCandidateID = previous.candidateID
        switch previous.screen {
        case .home:
            Task { await loadHome() }
        case .queue:
            if let candidateID = previous.candidateID {
                Task {
                    do {
                        try await loadCandidate(candidateID: candidateID)
                    } catch {
                        errorMessage = error.localizedDescription
                    }
                }
            } else {
                Task { await loadQueueAndDetail() }
            }
        case .daemon:
            Task { await loadDaemon() }
        }
    }

    func openCandidate(_ candidateID: String, recordHistory: Bool = true) {
        navigate(to: .queue, candidateID: candidateID, recordHistory: recordHistory)
        selectedCandidateID = candidateID
        Task {
            do {
                try await loadCandidate(candidateID: candidateID)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    func chooseCandidate(_ candidateID: String) {
        selectedCandidateID = candidateID
        Task {
            do {
                try await loadCandidate(candidateID: candidateID)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    var selectedCandidateIndex: Int? {
        guard
            let selectedCandidateID,
            let items = queueState?.items
        else {
            return nil
        }
        return items.firstIndex { $0.id == selectedCandidateID }
    }

    var hasPreviousCandidate: Bool {
        guard let selectedCandidateIndex else { return false }
        return selectedCandidateIndex > 0
    }

    var hasNextCandidate: Bool {
        guard
            let selectedCandidateIndex,
            let count = queueState?.items.count
        else {
            return false
        }
        return selectedCandidateIndex < count - 1
    }

    func selectPreviousCandidate() {
        guard
            let selectedCandidateIndex,
            selectedCandidateIndex > 0,
            let previousID = queueState?.items[selectedCandidateIndex - 1].id
        else {
            return
        }
        chooseCandidate(previousID)
    }

    func selectNextCandidate() {
        guard
            let selectedCandidateIndex,
            let items = queueState?.items,
            selectedCandidateIndex < items.count - 1
        else {
            return
        }
        chooseCandidate(items[selectedCandidateIndex + 1].id)
    }

    func captureClipboard() async {
        guard let text = NSPasteboard.general.string(forType: .string), !text.isEmpty else {
            showActionFeedback(
                title: strings.text(.actionFailed),
                message: strings.text(.clipboardEmpty),
                tone: .critical
            )
            return
        }
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await bridgeClient.captureClipboard(text: text, locale: strings.language == .ja ? "ja" : "en")
            showActionFeedback(
                title: strings.text(.actionCompleted),
                message: strings.captureActionMessage(id: response.id),
                tone: .positive
            )
            lastCandidateAction = CandidateActionRecord(
                candidateIDs: [response.id],
                title: strings.text(.actionCompleted),
                message: strings.captureActionMessage(id: response.id),
                tone: .positive
            )
            await loadQueueAndDetail()
            if let id = queueState?.items.first?.id {
                selectedCandidateID = id
            }
            selectedScreen = .queue
            errorMessage = nil
        } catch {
            showActionFeedback(
                title: strings.text(.actionFailed),
                message: error.localizedDescription,
                tone: .critical
            )
        }
    }

    func openVaultSession(level: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            _ = try await bridgeClient.openVaultSession(
                level: level,
                purpose: "resident-app-\(level)",
                profileID: bridgeProfileID
            )
            await loadHome()
            showActionFeedback(
                title: strings.text(.actionCompleted),
                message: strings.vaultSessionOpenedMessage(level: level),
                tone: .positive
            )
            errorMessage = nil
        } catch {
            showActionFeedback(
                title: strings.text(.actionFailed),
                message: error.localizedDescription,
                tone: .critical
            )
        }
    }

    func lockAllVaultSessions() async {
        isLoading = true
        defer { isLoading = false }
        do {
            _ = try await bridgeClient.lockVaultSessions(closeAll: true)
            await loadHome()
            showActionFeedback(
                title: strings.text(.actionCompleted),
                message: strings.vaultSessionsLockedMessage(),
                tone: .positive
            )
            errorMessage = nil
        } catch {
            showActionFeedback(
                title: strings.text(.actionFailed),
                message: error.localizedDescription,
                tone: .critical
            )
        }
    }

    @discardableResult
    func evaluateSelected(level: Int) async -> Bool {
        guard let candidateID = selectedCandidateID else { return false }
        pendingCandidateActionRecord = CandidateActionRecord(
            candidateIDs: [candidateID],
            title: strings.text(.actionCompleted),
            message: strings.evaluateActionMessage(id: candidateID, level: level),
            tone: .positive
        )
        return await performMutation {
            _ = try await self.bridgeClient.evaluate(candidateID: candidateID, level: level)
            await self.loadQueueAndDetail()
            return self.strings.evaluateActionMessage(id: candidateID, level: level)
        }
    }

    @discardableResult
    func approveSelected() async -> Bool {
        guard let candidateID = selectedCandidateID else { return false }
        pendingCandidateActionRecord = CandidateActionRecord(
            candidateIDs: [candidateID],
            title: strings.text(.actionCompleted),
            message: strings.approveActionMessage(id: candidateID),
            tone: .positive
        )
        return await performMutation {
            _ = try await self.bridgeClient.approve(candidateID: candidateID)
            await self.loadQueueAndDetail()
            return self.strings.approveActionMessage(id: candidateID)
        }
    }

    @discardableResult
    func rejectSelected(reason: String?) async -> Bool {
        guard let candidateID = selectedCandidateID else { return false }
        pendingCandidateActionRecord = CandidateActionRecord(
            candidateIDs: [candidateID],
            title: strings.text(.actionCompleted),
            message: strings.rejectActionMessage(id: candidateID),
            tone: .positive
        )
        return await performMutation {
            _ = try await self.bridgeClient.reject(candidateID: candidateID, reason: reason)
            await self.loadQueueAndDetail()
            return self.strings.rejectActionMessage(id: candidateID)
        }
    }

    @discardableResult
    func reviseSelected(editedText: String, targetSection: String?, changeReason: String?) async -> Bool {
        guard let candidateID = selectedCandidateID else { return false }
        return await performMutation {
            let response = try await self.bridgeClient.revise(candidateID: candidateID, editedText: editedText, targetSection: targetSection, changeReason: changeReason)
            self.pendingCandidateActionRecord = CandidateActionRecord(
                candidateIDs: [candidateID, response.id],
                title: self.strings.text(.actionCompleted),
                message: self.strings.reviseActionMessage(id: response.id, originalID: candidateID),
                tone: .positive
            )
            await self.loadQueueAndDetail()
            self.selectedCandidateID = response.id
            try await self.loadCandidate(candidateID: response.id)
            return self.strings.reviseActionMessage(id: response.id, originalID: candidateID)
        }
    }

    func recoverSession() async {
        showActionFeedback(
            title: strings.text(.retry),
            message: strings.bridgeActionInProgressMessage(startingBridge: false),
            tone: .caution,
            showsProgress: true
        )
        await bridgeClient.resetSession()
        await bootstrapAndLoad()
        if errorMessage == nil, health != nil {
            showActionFeedback(
                title: strings.text(.actionCompleted),
                message: strings.text(.bridgeReconnectedMessage),
                tone: .positive
            )
        } else if let errorMessage {
            showActionFeedback(
                title: strings.text(.actionFailed),
                message: strings.bridgeRecoveryFailureMessage(strings.localizedBridgeErrorMessage(errorMessage)),
                tone: .critical
            )
        }
    }

    func performBridgeSuggestedAction() async {
        guard let health else {
            await startBridgeAndReload()
            return
        }
        switch health.status {
        case "ok", "healthy":
            showActionFeedback(
                title: strings.text(.refresh),
                message: strings.bridgeActionInProgressMessage(startingBridge: false),
                tone: .caution,
                showsProgress: true
            )
            await refreshCurrentScreen()
            if errorMessage == nil {
                showActionFeedback(
                    title: strings.text(.actionCompleted),
                    message: strings.text(.bridgeRefreshedMessage),
                    tone: .positive
                )
            }
        case "starting", "bootstrapping":
            showActionFeedback(
                title: strings.text(.retry),
                message: strings.bridgeActionInProgressMessage(startingBridge: false),
                tone: .caution,
                showsProgress: true
            )
            await bootstrapAndLoad()
            if errorMessage == nil, self.health != nil {
                showActionFeedback(
                    title: strings.text(.actionCompleted),
                    message: strings.text(.bridgeReconnectedMessage),
                    tone: .positive
                )
            } else if let errorMessage {
                showActionFeedback(
                    title: strings.text(.actionFailed),
                    message: strings.bridgeRecoveryFailureMessage(strings.localizedBridgeErrorMessage(errorMessage)),
                    tone: .critical
                )
            }
        default:
            await recoverSession()
        }
    }

    func startBridgeAndReload() async {
        isLoading = true
        defer { isLoading = false }
        showActionFeedback(
            title: strings.text(.startBridge),
            message: strings.bridgeActionInProgressMessage(startingBridge: true),
            tone: .caution,
            showsProgress: true
        )
        do {
            try BridgeLauncher.launchBridge()
            lastBridgeLaunchFailure = nil
            showActionFeedback(
                title: strings.text(.startBridge),
                message: strings.bridgeLaunchWarmupMessage(),
                tone: .caution,
                showsProgress: true
            )
            await waitForBridgeWarmup()
            await bridgeClient.resetSession()
            await bootstrapAndLoad()
            if errorMessage == nil, health != nil {
                showActionFeedback(
                    title: strings.text(.actionCompleted),
                    message: strings.text(.bridgeStartedMessage),
                    tone: .positive
                )
            } else if let errorMessage {
                showActionFeedback(
                    title: strings.text(.actionFailed),
                    message: strings.localizedBridgeErrorMessage(errorMessage),
                    tone: .critical
                )
            }
        } catch {
            errorMessage = error.localizedDescription
            lastBridgeLaunchFailure = error.localizedDescription
            showActionFeedback(
                title: strings.text(.actionFailed),
                message: strings.bridgeRecoveryFailureMessage(strings.localizedBridgeErrorMessage(error.localizedDescription)),
                tone: .critical
            )
        }
    }

    private func waitForBridgeWarmup(
        timeoutNanoseconds: UInt64 = 8_000_000_000,
        pollNanoseconds: UInt64 = 250_000_000
    ) async {
        let start = DispatchTime.now().uptimeNanoseconds
        while DispatchTime.now().uptimeNanoseconds - start < timeoutNanoseconds {
            do {
                _ = try await bridgeClient.health()
                return
            } catch {
            }
            try? await Task.sleep(nanoseconds: pollNanoseconds)
        }
    }

    func openLogFile() {
        NSWorkspace.shared.open(bridgeClient.configuration.logFileURL)
    }

    func openTokenFile() {
        NSWorkspace.shared.open(bridgeClient.configuration.tokenFileURL)
    }

    func openDebugShell() {
        NSWorkspace.shared.open(bridgeClient.configuration.debugShellEntryURL(token: bridgeBootstrapToken))
    }

    func copyHealthCheckCommand() {
        copyToClipboard(
            "curl -s \(bridgeHealthURLText)",
            message: strings.copiedCommandMessage(context: strings.text(.healthEndpoint))
        )
    }

    func copyStartupCommand() {
        guard let startupCommandText else { return }
        copyToClipboard(
            startupCommandText,
            message: strings.copiedCommandMessage(context: strings.text(.startupCommand))
        )
    }

    func copyDebugShellURL() {
        copyToClipboard(
            bridgeDebugShellEntryURLText,
            message: strings.copiedCommandMessage(context: strings.text(.debugShell))
        )
    }

    func launchSourcePath() -> String? {
        let value = bridgeLaunchSourceText
        guard let index = value.firstIndex(of: ":") else { return nil }
        let path = value[value.index(after: index)...].trimmingCharacters(in: .whitespacesAndNewlines)
        guard path.hasPrefix("/") else { return nil }
        return path
    }

    func openLaunchSource() {
        openPath(launchSourcePath())
    }

    func copyLaunchSource() {
        copyToClipboard(
            bridgeLaunchSourceText,
            message: strings.copiedCommandMessage(context: strings.text(.launchSource))
        )
    }

    func resolvedLocalCommandPath(_ command: String) -> String? {
        let trimmed = command.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        guard let token = trimmed.split(whereSeparator: \.isWhitespace).first else { return nil }
        let pathToken = String(token)
        if pathToken.hasPrefix("/") {
            let path = URL(fileURLWithPath: pathToken).standardizedFileURL.path
            return FileManager.default.fileExists(atPath: path) ? path : nil
        }
        if pathToken.hasPrefix("./"), let repoRoot = BridgeLauncher.resolveRepoRoot() {
            let relativePath = String(pathToken.dropFirst(2))
            let path = repoRoot.appendingPathComponent(relativePath).standardizedFileURL.path
            return FileManager.default.fileExists(atPath: path) ? path : nil
        }
        return nil
    }

    func openCommandPath(_ command: String) {
        openPath(resolvedLocalCommandPath(command))
    }

    func openURLString(_ value: String?) {
        guard let rawValue = value else { return }
        let trimmed = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        guard let url = URL(string: trimmed) else { return }
        NSWorkspace.shared.open(url)
    }

    func openPath(_ path: String?) {
        guard let path, !path.isEmpty else { return }
        NSWorkspace.shared.open(URL(fileURLWithPath: path))
    }

    func openLaunchAgentPlist() {
        openPath(daemonState?.launchagentSummary.plistPath)
    }

    func openRuntimeDirectory() {
        if let runtimeRoot = daemonState?.runtimeInit["runtime_root"]?.stringValue {
            openPath(runtimeRoot)
            return
        }
        if let stdoutPath = daemonState?.launchagentPreview?["stdout_path"]?.stringValue {
            openPath(URL(fileURLWithPath: stdoutPath).deletingLastPathComponent().path)
        }
    }

    func copyToClipboard(_ value: String, message: String? = nil) {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(value, forType: .string)
        showActionFeedback(
            title: strings.text(.actionCompleted),
            message: message ?? value,
            tone: .positive
        )
    }

    func copyLaunchAgentCommand(_ action: String) {
        guard let command = daemonState?.launchagentSummary.launchctlCommands?[action] else { return }
        copyToClipboard(command, message: strings.copiedCommandMessage(context: strings.tokenLabel(action)))
    }

    func copyLaunchAgentPlistXML() {
        guard let xml = daemonState?.launchagentPreview?["plist_xml"]?.stringValue else { return }
        copyToClipboard(xml, message: strings.text(.copiedCommand))
    }

    func copyLaunchAgentLogTailCommand(kind: String) {
        let key = kind == "stderr" ? "stderr_path" : "stdout_path"
        guard let path = daemonState?.launchagentPreview?[key]?.stringValue else { return }
        copyToClipboard("tail -f \(path)", message: strings.copiedCommandMessage(context: strings.fieldLabel(kind)))
    }

    func candidateDetailClipboardText() -> String? {
        guard let detailState else { return nil }
        var lines: [String] = []
        if let candidateID = selectedCandidateID {
            lines.append("\(strings.text(.currentCandidate)): \(candidateID)")
        }
        let summary = detailState.uiSummary
        lines.append("\(strings.fieldLabel("status")): \(summary.status.map(strings.statusValueLabel) ?? strings.text(.none))")
        lines.append("\(strings.fieldLabel("section")): \(summary.section.map(strings.residentValueLabel) ?? strings.text(.none))")
        lines.append("\(strings.fieldLabel("operation")): \(summary.operation.map(strings.residentValueLabel) ?? strings.text(.none))")
        lines.append("\(strings.fieldLabel("rde")): \(summary.rdeClass.map(strings.residentValueLabel) ?? strings.text(.none))")
        if let sourceType = summary.sourceType {
            lines.append("\(strings.fieldLabel("source_type")): \(strings.residentValueLabel(sourceType))")
        }
        if let evaluationLevel = summary.evaluationLevel {
            lines.append("\(strings.text(.evaluateLevel)): \(strings.evaluationLevelLabel(evaluationLevel))")
        }
        if let content = detailState.content, !content.isEmpty {
            lines.append("")
            lines.append(strings.text(.detail))
            lines.append(content)
        }
        return lines.isEmpty ? nil : lines.joined(separator: "\n")
    }

    func candidateDiffClipboardText() -> String? {
        guard let diffState else { return nil }
        var lines: [String] = [strings.text(.diff)]
        if let section = diffState.section {
            lines.append("\(strings.fieldLabel("section")): \(strings.residentValueLabel(section))")
        }
        if let recommendedSection = diffState.recommendedSection {
            lines.append("\(strings.fieldLabel("recommended_section")): \(strings.residentValueLabel(recommendedSection))")
        }
        if let reviewSurface = diffState.reviewSurface {
            lines.append("\(strings.fieldLabel("review_surface")): \(strings.residentValueLabel(reviewSurface))")
        }
        if let note = diffState.note, !note.isEmpty {
            lines.append("")
            lines.append(note)
        }
        func appendList(_ title: String, prefix: String, items: [String]?) {
            guard let items, !items.isEmpty else { return }
            lines.append("")
            lines.append(title)
            lines.append(contentsOf: items.map { "\(prefix) \($0)" })
        }
        appendList(strings.text(.addedItems), prefix: "+", items: diffState.add)
        appendList(strings.text(.removedItems), prefix: "-", items: diffState.remove)
        appendList(strings.text(.existingItems), prefix: "•", items: diffState.alreadyPresent)
        return lines.joined(separator: "\n")
    }

    func candidateLineageClipboardText() -> String? {
        guard let lineageState else { return nil }
        var lines: [String] = [strings.text(.lineage), lineageState.candidateId]
        for entry in lineageState.lineageEntries ?? [] {
            lines.append("")
            lines.append(entry.summary)
            for key in entry.details.keys.sorted() {
                lines.append("\(strings.lineageDetailLabel(key)): \(entry.details[key] ?? "")")
            }
        }
        return lines.joined(separator: "\n")
    }

    func copySelectedCandidateDetail() {
        guard let value = candidateDetailClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.detail)))
    }

    func copySelectedCandidateDiff() {
        guard let value = candidateDiffClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.diff)))
    }

    func copySelectedCandidateLineage() {
        guard let value = candidateLineageClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.lineage)))
    }

    func launchAgentCurrentStateClipboardText() -> String? {
        guard let daemonState else { return nil }
        var lines: [String] = [strings.text(.currentState)]
        lines.append("\(strings.fieldLabel("plist_path")): \(daemonState.launchagentSummary.plistPath ?? strings.text(.none))")
        lines.append("\(strings.text(.loadedStatus)): \(daemonState.launchagentSummary.loadedStatus.map(strings.tokenLabel) ?? strings.text(.none))")
        if let returnCode = daemonState.launchagentStatus?["returncode"]?.displayText {
            lines.append("\(strings.text(.returnCode)): \(returnCode)")
        }
        if let printCommand = daemonState.launchagentStatus?["print_command"]?.stringValue {
            lines.append("\(strings.text(.nextCommand)): \(printCommand)")
        }
        return lines.joined(separator: "\n")
    }

    func launchAgentRecoveryPreviewClipboardText() -> String? {
        guard daemonState != nil else { return nil }
        var lines: [String] = [strings.text(.reviewPreviews)]
        lines.append("\(strings.diagnosticSummaryLabel("runtime_init")): \(strings.runtimeInitSummary(reviewRequired: runtimeInitReviewRequired, itemCount: runtimeInitItemCount))")
        lines.append("\(strings.diagnosticSummaryLabel("cleanup_preview")): \(strings.cleanupSummary(removeCount: cleanupRemoveCount, totalCount: cleanupTotalCount))")
        lines.append("\(strings.diagnosticSummaryLabel("repair_preview")): \(repairSummaryText)")
        let diagnostics = launchAgentDiagnosticMessages
        if !diagnostics.isEmpty {
            lines.append("")
            lines.append(contentsOf: diagnostics)
        }
        return lines.joined(separator: "\n")
    }

    func copyLaunchAgentCurrentState() {
        guard let value = launchAgentCurrentStateClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.currentState)))
    }

    func copyLaunchAgentRecoveryPreview() {
        guard let value = launchAgentRecoveryPreviewClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.reviewPreviews)))
    }

    func daemonOperatorSummaryClipboardText() -> String? {
        guard let daemonState else { return nil }
        var lines: [String] = [strings.text(.operatorSummaryRail)]
        lines.append("\(strings.fieldLabel("phase")): \(daemonState.operatorPhaseSummary.phase.map(strings.tokenLabel) ?? strings.text(.none))")
        lines.append("\(strings.fieldLabel("status")): \(daemonState.operatorPhaseSummary.phaseStatus.map(strings.tokenLabel) ?? strings.text(.none))")
        lines.append("\(strings.fieldLabel("readiness")): \(daemonState.operatorPhaseSummary.phaseReadiness.map(strings.tokenLabel) ?? strings.text(.none))")
        if let blocker = daemonState.operatorPhaseSummary.blockingReasons.first {
            lines.append("\(strings.text(.currentGate)): \(strings.tokenLabel(blocker))")
        }
        if let nextAction = daemonState.nextActions.first {
            lines.append("\(strings.text(.nextCommand)): \(nextAction.command)")
            if !nextAction.reason.isEmpty {
                lines.append("\(strings.text(.reason)): \(strings.operatorReasonLabel(nextAction.reason))")
            }
        }
        let readSurfaces = Array(daemonState.operatorPhaseDetails.readSurfaces.prefix(3))
        if !readSurfaces.isEmpty {
            lines.append("")
            lines.append(strings.text(.nextReadSurface))
            lines.append(contentsOf: readSurfaces.map { "• \($0)" })
        }
        let implementationOrder = Array(daemonState.operatorPhaseDetails.recommendedImplementationOrder.prefix(3))
        if !implementationOrder.isEmpty {
            lines.append("")
            lines.append(strings.text(.implementationOrder))
            lines.append(contentsOf: implementationOrder.enumerated().map { "\($0.offset + 1). \(strings.summaryCardLabel($0.element))" })
        }
        return lines.joined(separator: "\n")
    }

    func daemonPhaseGatesClipboardText() -> String? {
        guard let checklist = daemonState?.operatorPhaseStatus?["phase_closure_checklist"]?.arrayValue, !checklist.isEmpty else {
            return nil
        }
        var lines: [String] = [strings.text(.phaseClosureGates)]
        for value in checklist {
            guard let object = value.objectValue else { continue }
            let item = object["item"]?.stringValue.map(strings.phaseChecklistItemLabel) ?? strings.text(.none)
            let status = object["status"]?.stringValue.map(strings.tokenLabel) ?? strings.text(.none)
            lines.append("")
            lines.append("\(item): \(status)")
            let blockers = object["blocking_reasons"]?.arrayValue?.compactMap(\.stringValue) ?? []
            if blockers.isEmpty {
                lines.append("\(strings.text(.blockedBy)): \(strings.text(.none))")
            } else {
                lines.append("\(strings.text(.blockedBy)): \(strings.tokenLabel(blockers[0]))")
                if blockers.count > 1 {
                    lines.append(contentsOf: blockers.dropFirst().map { "• \(strings.tokenLabel($0))" })
                }
            }
        }
        return lines.joined(separator: "\n")
    }

    func daemonReadSurfacesClipboardText() -> String? {
        guard let daemonState else { return nil }
        let readSurfaces = daemonState.operatorPhaseDetails.readSurfaces
        guard !readSurfaces.isEmpty else { return nil }
        var lines: [String] = [strings.text(.readSurfaces)]
        lines.append(contentsOf: readSurfaces.enumerated().map { "\($0.offset + 1). \($0.element)" })
        return lines.joined(separator: "\n")
    }

    func daemonSuggestedActionsClipboardText() -> String? {
        guard let daemonState else { return nil }
        let actions = daemonState.nextActions
        guard !actions.isEmpty else { return nil }
        var lines: [String] = [strings.text(.suggestedAction)]
        for action in actions {
            lines.append("")
            lines.append(action.command)
            if !action.reason.isEmpty {
                lines.append("\(strings.text(.reason)): \(strings.operatorReasonLabel(action.reason))")
            }
        }
        return lines.joined(separator: "\n")
    }

    func copyDaemonOperatorSummary() {
        guard let value = daemonOperatorSummaryClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.operatorSummaryRail)))
    }

    func copyDaemonPhaseGates() {
        guard let value = daemonPhaseGatesClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.phaseClosureGates)))
    }

    func copyDaemonReadSurfaces() {
        guard let value = daemonReadSurfacesClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.readSurfaces)))
    }

    func copyDaemonSuggestedActions() {
        guard let value = daemonSuggestedActionsClipboardText() else { return }
        copyToClipboard(value, message: strings.copiedCommandMessage(context: strings.text(.suggestedAction)))
    }

    func daemonHandoffExportText() -> String? {
        guard let daemonState else { return nil }
        var sections: [String] = []
        sections.append(strings.text(.handoffSnapshot))
        sections.append("")
        sections.append("\(strings.text(.bridgeContext)):")
        sections.append("\(strings.text(.generatedAt)): \(handoffExportTimestampText())")
        sections.append("\(strings.text(.profile)): \(bridgeProfileID)")
        sections.append("\(strings.text(.bridgeURL)): \(bridgeBaseURLText)")
        sections.append("\(strings.text(.healthEndpoint)): \(bridgeHealthURLText)")
        sections.append("\(strings.text(.debugShell)): \(bridgeDebugShellEntryURLText)")
        sections.append("\(strings.text(.tokenFile)): \(bridgeTokenFilePath)")
        sections.append("\(strings.text(.logFile)): \(bridgeLogFilePath)")
        sections.append("\(strings.text(.bridgeStatusPanel)): \(bridgeStatusHeadline)")
        sections.append(bridgeStatusDetail)
        if let health {
            if let component = health.component, !component.isEmpty {
                sections.append("\(strings.text(.component)): \(component)")
            }
            sections.append("\(strings.text(.bridgeVersion)): \(health.version ?? "-")")
            if let sourceUpdatedAt = health.sourceUpdatedAt, !sourceUpdatedAt.isEmpty {
                sections.append("\(strings.text(.sourceUpdatedAt)): \(sourceUpdatedAt)")
            }
        }
        sections.append("")
        sections.append("\(strings.fieldLabel("phase")): \(daemonState.operatorPhaseSummary.phase.map(strings.tokenLabel) ?? strings.text(.none))")
        sections.append("\(strings.fieldLabel("status")): \(daemonState.operatorPhaseSummary.phaseStatus.map(strings.tokenLabel) ?? strings.text(.none))")
        sections.append("\(strings.fieldLabel("readiness")): \(daemonState.operatorPhaseSummary.phaseReadiness.map(strings.tokenLabel) ?? strings.text(.none))")
        sections.append("")
        sections.append("\(strings.text(.statusDiagnostics)):")
        if let firstAction = daemonState.nextActions.first {
            sections.append("• \(strings.text(.nextCommand)): \(firstAction.command)")
            if !firstAction.reason.isEmpty {
                sections.append("• \(strings.text(.reason)): \(strings.operatorReasonLabel(firstAction.reason))")
            }
        }
        if let printCommand = daemonState.launchagentStatus?["print_command"]?.stringValue, !printCommand.isEmpty {
            sections.append("• \(strings.text(.launchctlPrint)): \(printCommand)")
        }
        sections.append("")
        sections.append("\(strings.text(.tailLogs)):")
        if let stdoutTail = launchAgentLogTailCommand(kind: "stdout") {
            sections.append("• \(strings.text(.stdoutTail)): \(stdoutTail)")
        }
        if let stderrTail = launchAgentLogTailCommand(kind: "stderr") {
            sections.append("• \(strings.text(.stderrTail)): \(stderrTail)")
        }
        let preflight = preflightChecksForExport()
        if !preflight.isEmpty {
            sections.append("")
            sections.append("\(strings.text(.preflightChecks)):")
            sections.append(contentsOf: preflight.map { "• \($0)" })
        }
        let proof = proofDiagnosticCommandsForExport()
        if !proof.isEmpty {
            sections.append("")
            sections.append("\(strings.text(.proofDiagnostics)):")
            sections.append(contentsOf: proof.map { "• \($0)" })
        }

        if let operatorSummary = daemonOperatorSummaryClipboardText(), !operatorSummary.isEmpty {
            sections.append("")
            sections.append("\(strings.text(.operatorSummaryRail)):")
            sections.append(operatorSummary)
        }
        if let actions = daemonSuggestedActionsClipboardText(), !actions.isEmpty {
            sections.append("")
            sections.append("\(strings.text(.suggestedAction)):")
            sections.append(actions)
        }
        if let gates = daemonPhaseGatesClipboardText(), !gates.isEmpty {
            sections.append("")
            sections.append("\(strings.text(.phaseClosureGates)):")
            sections.append(gates)
        }
        if let surfaces = daemonReadSurfacesClipboardText(), !surfaces.isEmpty {
            sections.append("")
            sections.append("\(strings.text(.readSurfaces)):")
            sections.append(surfaces)
        }
        if let currentState = launchAgentCurrentStateClipboardText(), !currentState.isEmpty {
            sections.append("")
            sections.append("\(strings.text(.currentState)):")
            sections.append(currentState)
        }
        if let recoveryPreview = launchAgentRecoveryPreviewClipboardText(), !recoveryPreview.isEmpty {
            sections.append("")
            sections.append("\(strings.text(.reviewPreviews)):")
            sections.append(recoveryPreview)
        }

        return sections.joined(separator: "\n")
    }

    func daemonHandoffExportFilename() -> String {
        "sayane-daemon-handoff-\(handoffExportFilenameTimestampText()).txt"
    }

    func exportDaemonHandoffNote() {
        guard let value = daemonHandoffExportText(), !value.isEmpty else { return }
        exportTextToFile(
            value,
            suggestedName: daemonHandoffExportFilename()
        )
    }

    func openQuickLink(_ link: QuickLink) {
        switch link.screen {
        case "candidate_queue":
            let firstID = selectedCandidateID ?? queueState?.items.first?.id
            navigate(to: .queue, candidateID: firstID, recordHistory: true)
            if let firstID {
                chooseCandidate(firstID)
            }
        case "daemon_panel":
            navigate(to: .daemon, candidateID: nil, recordHistory: true)
        default:
            break
        }
    }

    private func candidateIDForScreen(_ screen: Screen) -> String? {
        switch screen {
        case .queue:
            selectedCandidateID
        case .home, .daemon:
            nil
        }
    }

    private func currentNavigationState() -> NavigationState {
        NavigationState(screen: selectedScreen, candidateID: candidateIDForScreen(selectedScreen))
    }

    private func navigate(to screen: Screen, candidateID: String?, recordHistory: Bool) {
        let current = currentNavigationState()
        let target = NavigationState(screen: screen, candidateID: screen == .queue ? candidateID : nil)
        if recordHistory, current != target {
            backStack.append(current)
        }
        selectedScreen = screen
        if screen == .queue {
            selectedCandidateID = candidateID
        }
    }

    func dismissActionFeedback() {
        actionTitle = nil
        actionMessage = nil
        actionTone = .positive
        actionShowsProgress = false
    }

    private func showActionFeedback(title: String, message: String, tone: StatusTone, showsProgress: Bool = false) {
        actionTitle = title
        actionMessage = message
        actionTone = tone
        actionShowsProgress = showsProgress
    }

    private func handoffExportTimestampText(now: Date = Date()) -> String {
        ISO8601DateFormatter().string(from: now)
    }

    private func handoffExportFilenameTimestampText(now: Date = Date()) -> String {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone.current
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        return formatter.string(from: now)
    }

    private func launchAgentLogTailCommand(kind: String) -> String? {
        let key = kind == "stderr" ? "stderr_path" : "stdout_path"
        guard let path = daemonState?.launchagentPreview?[key]?.stringValue, !path.isEmpty else { return nil }
        return "tail -f \(path)"
    }

    private func preflightChecksForExport() -> [String] {
        [
            "sayane init",
            "sayane serve --host 127.0.0.1 --port 38741",
            "curl -s http://127.0.0.1:38741/health",
            "sayane app daemon-preflight --json",
            "sayane app daemon-preflight --json --include-event-record",
            "which sayane",
        ]
    }

    private func proofDiagnosticCommandsForExport() -> [String] {
        [
            "sayane app daemon-identity-proof --json",
            "sayane app daemon-readiness-proof --operation-class bridge_health --json",
            "sayane app daemon-api-readiness-proof --operation-class bridge_health --json",
            "sayane app daemon-proof-diagnostics --operation-class bridge_health --json",
        ]
    }

    private func exportTextToFile(_ value: String, suggestedName: String) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = suggestedName
        panel.allowedContentTypes = [.plainText]
        panel.canCreateDirectories = true
        panel.isExtensionHidden = false
        if panel.runModal() == .OK, let url = panel.url {
            do {
                try value.write(to: url, atomically: true, encoding: .utf8)
                showActionFeedback(
                    title: strings.text(.savedFile),
                    message: strings.savedFileMessage(path: url.path),
                    tone: .positive
                )
            } catch {
                showActionFeedback(
                    title: strings.text(.actionFailed),
                    message: error.localizedDescription,
                    tone: .critical
                )
            }
        }
    }

    private func performMutation(_ operation: @escaping () async throws -> String?) async -> Bool {
        isLoading = true
        defer { isLoading = false }
        do {
            let message = try await operation()
            errorMessage = nil
            if let message, !message.isEmpty {
                showActionFeedback(
                    title: strings.text(.actionCompleted),
                    message: message,
                    tone: .positive
                )
            }
            if let record = pendingCandidateActionRecord {
                lastCandidateAction = record
            }
            pendingCandidateActionRecord = nil
            return true
        } catch {
            showActionFeedback(
                title: strings.text(.actionFailed),
                message: error.localizedDescription,
                tone: .critical
            )
            if let record = pendingCandidateActionRecord {
                lastCandidateAction = CandidateActionRecord(
                    candidateIDs: record.candidateIDs,
                    title: strings.text(.actionFailed),
                    message: error.localizedDescription,
                    tone: .critical
                )
            }
            pendingCandidateActionRecord = nil
            return false
        }
    }

    private var pendingCandidateActionRecord: CandidateActionRecord?

    private var runtimeInitReviewRequired: Bool {
        daemonState?.runtimeInit["review_required"]?.boolValue ?? false
    }

    private var runtimeInitItemCount: Int {
        daemonState?.runtimeInit["items"]?.arrayValue?.count ?? 0
    }

    private var cleanupRemoveCount: Int {
        daemonState?.cleanupPreview["decision_report"]?.objectValue?["decisions"]?.arrayValue?.filter {
            $0.objectValue?["recommended_action"]?.stringValue == "remove"
        }.count ?? 0
    }

    private var cleanupTotalCount: Int {
        daemonState?.cleanupPreview["decision_report"]?.objectValue?["decisions"]?.arrayValue?.count ?? 0
    }

    private var repairSummaryText: String {
        let count = daemonState?.repairPreview["decisions"]?.objectValue?.count ?? 0
        if count == 0 {
            return strings.text(.none)
        }
        return strings.moreItemsMessage(count)
    }

    private var launchAgentDiagnosticMessages: [String] {
        var lines: [String] = []
        if let loaded = daemonState?.launchagentStatus?["loaded"]?.boolValue, loaded {
            lines.append(strings.diagnosticMessage("launchagent_loaded"))
        }
        if let printCommand = daemonState?.launchagentStatus?["print_command"]?.stringValue, !printCommand.isEmpty {
            lines.append(strings.diagnosticMessage("launchctl_print_available"))
        }
        if let stderr = daemonState?.launchagentStatus?["stderr"]?.stringValue, !stderr.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            lines.append(strings.diagnosticMessage("stderr_attention"))
        }
        return lines
    }
}
