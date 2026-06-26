import SwiftUI

struct HomeView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header
                BridgeStatusPanel(model: model)
                prioritySection
                BridgeDiagnosticsCard(model: model, compact: false)
                cardsSection
                quickLinksSection
                reviewSection
                daemonSection
            }
            .padding(24)
        }
        .navigationTitle(model.strings.text(.home))
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(model.strings.text(.appTitle)).font(.largeTitle).bold()
            if let health = model.health {
                Text("\(model.strings.text(.bridgeHealthy)): \(model.strings.summaryValueLabel(key: "state", value: health.status)) · \(health.version ?? "-")")
                    .foregroundStyle(.secondary)
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

    private var prioritySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.startHere))
            if priorityItems.isEmpty {
                StateCardView(
                    icon: "sparkles",
                    title: model.strings.text(.startHere),
                    message: model.strings.text(.noPriorityActions),
                    tone: .neutral,
                    badgeText: model.strings.text(.healthySignals),
                    actionTitle: model.strings.text(.refresh),
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                ForEach(priorityItems, id: \.title) { item in
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
            }
        }
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
                    actionTitle: model.strings.text(.refresh),
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                ForEach(model.homeState?.topReviewItems ?? []) { item in
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
                    actionTitle: model.strings.text(.refresh),
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                ForEach(model.homeState?.quickLinks ?? []) { link in
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
                ForEach(model.homeState?.topDaemonActions ?? [], id: \.self) { action in
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
