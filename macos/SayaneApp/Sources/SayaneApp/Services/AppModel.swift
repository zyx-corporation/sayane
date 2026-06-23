import AppKit
import Foundation
import SwiftUI

@MainActor
final class AppModel: ObservableObject {
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
    @Published var lastCandidateAction: CandidateActionRecord?
    @Published var showingReviseSheet = false
    @Published var showingRejectSheet = false
    @Published var showingEvaluateSheet = false

    let strings = AppStrings.current
    let bridgeClient: BridgeClient
    private var backStack: [NavigationState] = []

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
        } catch {
            errorMessage = error.localizedDescription
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

    func sidebarMetadata(for screen: Screen) -> SidebarMetadata {
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
        guard let health else {
            return strings.text(.bridgeStatusDetailDisconnected)
        }
        let versionText = health.version ?? "-"
        if let sourceUpdatedAt = health.sourceUpdatedAt, !sourceUpdatedAt.isEmpty {
            return "\(strings.text(.bridgeVersion)): \(versionText) · \(strings.text(.sourceUpdatedAt)): \(sourceUpdatedAt)"
        }
        return "\(strings.text(.bridgeVersion)): \(versionText)"
    }

    var bridgeSuggestedActionText: String {
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

    var bridgeBaseURLText: String {
        bridgeClient.configuration.baseURL.absoluteString
    }

    var bridgeHealthURLText: String {
        bridgeClient.configuration.healthURL.absoluteString
    }

    var bridgeDebugShellURLText: String {
        bridgeClient.configuration.debugShellURL.absoluteString
    }

    var bridgeTokenFilePath: String {
        bridgeClient.configuration.tokenFileURL.path
    }

    var bridgeLogFilePath: String {
        bridgeClient.configuration.logFileURL.path
    }

    var bridgeProfileID: String {
        bridgeClient.configuration.profileID
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
        await bridgeClient.resetSession()
        await bootstrapAndLoad()
    }

    func startBridgeAndReload() async {
        isLoading = true
        defer { isLoading = false }
        do {
            try BridgeLauncher.launchBridge()
            await bridgeClient.resetSession()
            await bootstrapAndLoad()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func openLogFile() {
        NSWorkspace.shared.open(bridgeClient.configuration.logFileURL)
    }

    func openTokenFile() {
        NSWorkspace.shared.open(bridgeClient.configuration.tokenFileURL)
    }

    func openDebugShell() {
        NSWorkspace.shared.open(bridgeClient.configuration.debugShellURL)
    }

    func copyHealthCheckCommand() {
        copyToClipboard(
            "curl -s \(bridgeHealthURLText)",
            message: strings.copiedCommandMessage(context: strings.text(.healthEndpoint))
        )
    }

    func copyDebugShellURL() {
        copyToClipboard(
            bridgeDebugShellURLText,
            message: strings.copiedCommandMessage(context: strings.text(.debugShell))
        )
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
    }

    private func showActionFeedback(title: String, message: String, tone: StatusTone) {
        actionTitle = title
        actionMessage = message
        actionTone = tone
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
}
