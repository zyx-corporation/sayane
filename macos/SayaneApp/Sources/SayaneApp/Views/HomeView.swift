import SwiftUI

struct HomeView: View {
    @ObservedObject var model: AppModel
    @State private var showsDiagnosticsSheet = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header
                BridgeStatusPanel(model: model, compact: true)
                launcherSection
                if showsBridgeDiagnostics {
                    diagnosticsPromptCard
                }
                cardsSection
                vaultSection
                reviewSection
                daemonSection
                quickLinksSection
            }
            .padding(24)
        }
        .navigationTitle(model.strings.text(.home))
        .sheet(isPresented: $showsDiagnosticsSheet) {
            DiagnosticsSheetView(model: model)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(model.strings.text(.appTitle)).font(.largeTitle).bold()
                    Text(model.homeBridgeSummaryText)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Button(model.strings.text(.captureClipboard)) {
                    Task { await model.captureClipboard() }
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }

    private var launcherSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.startHere))
            if priorityItems.isEmpty,
               model.homeState?.topReviewItems.first == nil,
               model.homeState?.topDaemonActions.first == nil
            {
                StateCardView(
                    icon: "sparkles",
                    title: model.strings.text(.startHere),
                    message: model.homePriorityEmptyMessage,
                    tone: .neutral,
                    badgeText: model.homePriorityEmptyBadgeText,
                    actionTitle: model.toolbarRefreshText,
                    actionEnabled: !model.bridgeRecoveryActionDisabled,
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 260), spacing: 12)], spacing: 12) {
                    ForEach(Array(priorityItems.prefix(2).enumerated()), id: \.offset) { _, item in
                        Button(action: item.action) {
                            SurfaceCard(emphasis: 0.38) {
                                HStack(alignment: .top, spacing: 12) {
                                    StatusBadge(text: item.badge, tone: item.tone)
                                    CardTitleSummary(title: item.title, summary: item.summary)
                                    Spacer()
                                    Image(systemName: "arrow.right.circle.fill")
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("\(item.badge) \(item.title) \(item.summary)")
                    }

                    if let review = model.homeState?.topReviewItems.first {
                        Button {
                            model.openCandidate(review.candidateId)
                        } label: {
                            SurfaceCard(emphasis: 0.28) {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack(alignment: .top, spacing: 8) {
                                        CardTitleSummary(
                                            title: model.strings.text(.reviewNextCandidate),
                                            summary: homeReviewItemSummary(review)
                                        )
                                        Spacer()
                                        if let status = review.status {
                                            StatusBadge(
                                                text: model.strings.statusValueLabel(status),
                                                tone: model.strings.tone(forToken: status)
                                            )
                                        }
                                    }
                                    Text(review.candidateId)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("\(model.strings.text(.reviewNextCandidate)) \(review.candidateId) \(homeReviewItemSummary(review))")
                    }

                    if let action = model.homeState?.topDaemonActions.first {
                        Button {
                            model.choose(screen: .daemon)
                        } label: {
                            SurfaceCard(emphasis: 0.24) {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack {
                                        StatusBadge(
                                            text: homeDaemonActionTitle(action),
                                            tone: homeDaemonActionTone(action)
                                        )
                                        Spacer()
                                    }
                                    Text(homeDaemonActionSummary(action))
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    CommandRowView(command: action, lineLimit: 2)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("\(homeDaemonActionTitle(action)) \(homeDaemonActionSummary(action))")
                    }
                }
            }
        }
    }

    private var cardsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.summaryCards))
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 180))], spacing: 12) {
                ForEach(model.homeState?.summaryCards ?? []) { card in
                    SurfaceCard(emphasis: 0.4) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.summaryCardLabel(card.key)).font(.caption).foregroundStyle(.secondary)
                            SummaryCardValueView(strings: model.strings, card: card)
                        }
                    }
                }
            }
        }
    }

    private var diagnosticsPromptCard: some View {
        StateCardView(
            icon: "stethoscope",
            title: model.strings.text(.connectionDiagnostics),
            message: model.bridgeStatusDetail,
            tone: model.bridgeStatusTone,
            badgeText: model.bridgeStatusText,
            actionTitle: model.strings.text(.troubleshooting),
            action: { showsDiagnosticsSheet = true }
        )
    }

    private var reviewSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.topReviewItems))
            if (model.homeState?.topReviewItems ?? []).isEmpty {
                StateCardView(
                    icon: "tray",
                    title: model.strings.text(.topReviewItems),
                    message: model.strings.text(.noReviewItems),
                    tone: .neutral,
                    actionTitle: model.toolbarRefreshText,
                    actionEnabled: !model.bridgeRecoveryActionDisabled,
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                ForEach(reviewPreviewItems) { item in
                    Button {
                        model.openCandidate(item.candidateId)
                    } label: {
                        SurfaceCard {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(item.candidateId).font(.headline)
                                Text(homeReviewItemSummary(item))
                                    .foregroundStyle(.secondary)
                                if let status = item.status {
                                    StatusBadge(
                                        text: model.strings.statusValueLabel(status),
                                        tone: model.strings.tone(forToken: status)
                                    )
                                }
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("\(item.candidateId) \(homeReviewItemSummary(item))")
                }
                if reviewOverflowCount > 0 {
                    Text(model.strings.moreItemsMessage(reviewOverflowCount))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private var quickLinksSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.quickLinks))
            if (model.homeState?.quickLinks ?? []).isEmpty {
                StateCardView(
                    icon: "link",
                    title: model.strings.text(.quickLinks),
                    message: model.strings.text(.noQuickLinks),
                    tone: .neutral,
                    actionTitle: model.toolbarRefreshText,
                    actionEnabled: !model.bridgeRecoveryActionDisabled,
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                ForEach(quickLinkPreviewItems) { link in
                    Button {
                        model.openQuickLink(link)
                    } label: {
                        SurfaceCard {
                            HStack {
                                CardTitleSummary(
                                    title: model.strings.quickLinkLabel(screen: link.screen),
                                    summary: quickLinkSummary(link)
                                )
                                Spacer()
                                Image(systemName: "arrow.right.circle.fill")
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(model.strings.quickLinkLabel(screen: link.screen))
                }
                if quickLinkOverflowCount > 0 {
                    Text(model.strings.moreItemsMessage(quickLinkOverflowCount))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private var vaultSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.localVault))
            if let summary = model.homeState?.vaultSummary {
                SurfaceCard {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack {
                            StatusBadge(
                                text: model.strings.summaryValueLabel(key: "vault_status", value: summary.status ?? "unavailable"),
                                tone: model.strings.tone(forToken: summary.status ?? "unavailable")
                            )
                            Spacer()
                            if let assurance = summary.assurance, !assurance.isEmpty {
                                StatusBadge(
                                    text: model.strings.summaryValueLabel(key: "vault_assurance", value: assurance),
                                    tone: model.strings.tone(forToken: assurance)
                                )
                            }
                        }
                        if let backend = summary.backend, !backend.isEmpty {
                            DetailLabelValueRow(
                                label: model.strings.text(.backend),
                                value: model.strings.summaryValueLabel(key: "vault_backend", value: backend)
                            )
                        }
                        if let path = summary.vaultPath, !path.isEmpty {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(model.strings.text(.vaultPath))
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(.secondary)
                                SelectableMonospaceText(text: path)
                            }
                        }
                        if let supports = summary.supportsScopedUnlockSessions {
                            DetailLabelValueRow(
                                label: model.strings.text(.vaultSessions),
                                value: supports ? model.strings.text(.supported) : model.strings.text(.notSupported)
                            )
                        }
                        if let sessionStatus = summary.sessionStatus {
                            DetailLabelValueRow(
                                label: model.strings.text(.activeSessions),
                                value: "\(sessionStatus.activeSessionCount)"
                            )
                            if !sessionStatus.activeSessions.isEmpty {
                                VStack(alignment: .leading, spacing: 8) {
                                    ForEach(sessionStatus.activeSessions.prefix(2)) { session in
                                        SurfaceCard(emphasis: 0.18) {
                                            VStack(alignment: .leading, spacing: 6) {
                                                HStack {
                                                    if let level = session.level {
                                                        StatusBadge(
                                                            text: model.strings.tokenLabel(level),
                                                            tone: model.strings.tone(forToken: level)
                                                        )
                                                    }
                                                    if let assurance = session.assurance {
                                                        StatusBadge(
                                                            text: model.strings.tokenLabel(assurance),
                                                            tone: model.strings.tone(forToken: assurance)
                                                        )
                                                    }
                                                }
                                                if let purpose = session.purpose, !purpose.isEmpty {
                                                    DetailLabelValueRow(
                                                        label: model.strings.text(.sessionPurpose),
                                                        value: purpose
                                                    )
                                                }
                                                if let expiresAt = session.expiresAt, !expiresAt.isEmpty {
                                                    DetailLabelValueRow(
                                                        label: model.strings.text(.expiresAt),
                                                        value: expiresAt
                                                    )
                                                }
                                                if let idleExpiresAt = session.idleExpiresAt, !idleExpiresAt.isEmpty {
                                                    DetailLabelValueRow(
                                                        label: model.strings.text(.idleExpiresAt),
                                                        value: idleExpiresAt
                                                    )
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            if !sessionStatus.availableLevels.isEmpty {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack(spacing: 8) {
                                        Button(model.strings.text(.unlockNormal)) {
                                            Task { await model.openVaultSession(level: "normal") }
                                        }
                                        .buttonStyle(.bordered)
                                        Button(model.strings.text(.unlockSensitive)) {
                                            Task { await model.openVaultSession(level: "sensitive") }
                                        }
                                        .buttonStyle(.bordered)
                                        Button(model.strings.text(.unlockDeepPrivate)) {
                                            Task { await model.openVaultSession(level: "deep_private") }
                                        }
                                        .buttonStyle(.bordered)
                                    }
                                    Button(model.strings.text(.lockAll)) {
                                        Task { await model.lockAllVaultSessions() }
                                    }
                                    .buttonStyle(.bordered)
                                }
                            }
                        }
                        if !summary.unlockPolicies.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(model.strings.text(.unlockPolicies))
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(.secondary)
                                ForEach(summary.unlockPolicies.prefix(2)) { policy in
                                    Text("\(model.strings.tokenLabel(policy.level)) · idle \(policy.idleTimeoutSeconds)s / ttl \(policy.absoluteTimeoutSeconds)s")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        if let setup = summary.recommendedSetup, !setup.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(model.strings.text(.recommendedSetup))
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(.secondary)
                                ForEach(setup.keys.sorted(), id: \.self) { key in
                                    if let command = setup[key] {
                                        CommandRowView(command: command, lineLimit: 2)
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                StateCardView(
                    icon: "lock.shield",
                    title: model.strings.text(.localVault),
                    message: model.strings.text(.vaultUnavailable),
                    tone: .neutral,
                    actionTitle: model.toolbarRefreshText,
                    actionEnabled: !model.bridgeRecoveryActionDisabled,
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            }
        }
    }

    private var daemonSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.topDaemonActions))
            if (model.homeState?.topDaemonActions ?? []).isEmpty {
                StateCardView(
                    icon: "bolt.slash",
                    title: model.strings.text(.topDaemonActions),
                    message: model.strings.text(.noDaemonActions),
                    tone: .neutral,
                    actionTitle: model.strings.text(.daemon),
                    action: { model.choose(screen: .daemon) }
                )
            } else {
                ForEach(daemonActionPreviewItems, id: \.self) { action in
                    Button {
                        model.choose(screen: .daemon)
                    } label: {
                        SurfaceCard {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    StatusBadge(
                                        text: homeDaemonActionTitle(action),
                                        tone: homeDaemonActionTone(action)
                                    )
                                    Spacer()
                                }
                                Text(homeDaemonActionSummary(action))
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(model.strings.text(.nextCommand))
                                        .font(.caption.weight(.semibold))
                                    CommandRowView(command: action, lineLimit: 2)
                                }
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("\(homeDaemonActionTitle(action)) \(homeDaemonActionSummary(action))")
                }
                if daemonActionOverflowCount > 0 {
                    Text(model.strings.moreItemsMessage(daemonActionOverflowCount))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private func homeDaemonActionTitle(_ action: String) -> String {
        model.strings.commandPriorityTitle(for: action)
    }

    private func homeDaemonActionTone(_ action: String) -> StatusTone {
        model.strings.tone(forCommand: action)
    }

    private func homeDaemonActionSummary(_ action: String) -> String {
        model.strings.homeDaemonActionSummary(for: action)
    }

    private func homeReviewItemSummary(_ item: TopReviewItem) -> String {
        item.displaySummary
            ?? item.proposalSection.map(model.strings.residentValueLabel)
            ?? item.status.map(model.strings.statusValueLabel)
            ?? model.strings.text(.none)
    }

    private func quickLinkSummary(_ link: QuickLink) -> String {
        switch link.screen {
        case "candidate_queue":
            return model.strings.text(.selectCandidatePrompt)
        case "daemon_panel":
            return model.strings.text(.reviewDaemonAction)
        default:
            return "\(model.strings.text(.screenOverview)): \(link.path)"
        }
    }

    private var showsBridgeDiagnostics: Bool {
        if model.errorMessage != nil { return true }
        guard let status = model.health?.status.lowercased() else { return true }
        return status != "ok" && status != "healthy"
    }

    private var reviewPreviewItems: [TopReviewItem] {
        Array((model.homeState?.topReviewItems ?? []).prefix(2))
    }

    private var reviewOverflowCount: Int {
        max((model.homeState?.topReviewItems.count ?? 0) - reviewPreviewItems.count, 0)
    }

    private var quickLinkPreviewItems: [QuickLink] {
        Array((model.homeState?.quickLinks ?? []).prefix(3))
    }

    private var quickLinkOverflowCount: Int {
        max((model.homeState?.quickLinks.count ?? 0) - quickLinkPreviewItems.count, 0)
    }

    private var daemonActionPreviewItems: [String] {
        Array((model.homeState?.topDaemonActions ?? []).prefix(2))
    }

    private var daemonActionOverflowCount: Int {
        max((model.homeState?.topDaemonActions.count ?? 0) - daemonActionPreviewItems.count, 0)
    }

    private var priorityItems: [(title: String, summary: String, badge: String, tone: StatusTone, action: () -> Void)] {
        var items: [(String, String, String, StatusTone, () -> Void)] = []

        if let startupCommand = model.startupCommandText {
            items.append((
                model.strings.text(.supportedPath),
                startupCommand,
                model.strings.text(.recommended),
                .positive,
                { model.choose(screen: .daemon) }
            ))
        }

        if let review = model.homeState?.topReviewItems.first {
            items.append((
                model.strings.text(.reviewNextCandidate),
                homeReviewItemSummary(review),
                model.strings.text(.topReviewItems),
                .caution,
                { model.openCandidate(review.candidateId) }
            ))
        }

        if let link = model.homeState?.quickLinks.first {
            items.append((
                model.strings.quickLinkLabel(screen: link.screen),
                quickLinkSummary(link),
                model.strings.text(.quickLinks),
                .positive,
                { model.openQuickLink(link) }
            ))
        }

        if model.currentGateText == nil, model.nextDaemonCommandText == nil, model.nextReadSurfaceText == nil,
           let daemonAction = model.homeState?.topDaemonActions.first {
            items.append((
                model.strings.text(.reviewDaemonAction),
                homeDaemonActionSummary(daemonAction),
                homeDaemonActionTitle(daemonAction),
                homeDaemonActionTone(daemonAction),
                { model.choose(screen: .daemon) }
            ))
        }

        return items
    }
}
