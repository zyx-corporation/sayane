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
                Text("\(model.strings.text(.bridgeHealthy)): \(health.status) · \(health.version ?? "-")")
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
                            summaryValueView(card)
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
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(item.title)
                                        .font(.headline)
                                    Text(item.summary)
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                }
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
                                Text(item.displaySummary ?? item.proposalSection ?? item.status ?? model.strings.text(.none))
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
                    .accessibilityLabel("\(item.candidateId) \(item.displaySummary ?? item.proposalSection ?? item.status ?? model.strings.text(.none))")
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
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(model.strings.quickLinkLabel(screen: link.screen))
                                        .font(.headline)
                                    Text(link.path)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
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
                                Text(action)
                                    .font(.system(.body, design: .monospaced))
                                    .textSelection(.enabled)
                                Text(homeDaemonActionSummary(action))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("\(homeDaemonActionTitle(action)) \(homeDaemonActionSummary(action))")
                }
            }
        }
    }

    private func homeSummaryValue(_ card: SummaryCard) -> String {
        guard let value = card.value else {
            return model.strings.text(.none)
        }
        if let string = value.stringValue {
            return model.strings.summaryValueLabel(key: card.key, value: string)
        }
        return value.displayText
    }

    @ViewBuilder
    private func summaryValueView(_ card: SummaryCard) -> some View {
        if let string = card.value?.stringValue {
            StatusBadge(
                text: model.strings.summaryValueLabel(key: card.key, value: string),
                tone: model.strings.tone(forToken: string)
            )
        } else {
            Text(homeSummaryValue(card)).font(.headline)
        }
    }

    private func homeDaemonActionTitle(_ action: String) -> String {
        if action.contains("status") || action.contains("health") {
            return model.strings.text(.verifyNow)
        }
        if action.contains("start") || action.contains("bootstrap") || action.contains("kickstart") {
            return model.strings.text(.suggestedAction)
        }
        if action.contains("repair") || action.contains("cleanup") || action.contains("bootout") {
            return model.strings.text(.needsAttention)
        }
        return model.strings.text(.actionSummary)
    }

    private func homeDaemonActionTone(_ action: String) -> StatusTone {
        if action.contains("repair") || action.contains("cleanup") || action.contains("bootout") {
            return .critical
        }
        if action.contains("start") || action.contains("bootstrap") || action.contains("kickstart") {
            return .caution
        }
        if action.contains("status") || action.contains("health") {
            return .positive
        }
        return .neutral
    }

    private func homeDaemonActionSummary(_ action: String) -> String {
        model.strings.homeDaemonActionSummary(for: action)
    }

    private var priorityItems: [(title: String, summary: String, badge: String, tone: StatusTone, action: () -> Void)] {
        var items: [(String, String, String, StatusTone, () -> Void)] = []

        if let review = model.homeState?.topReviewItems.first {
            items.append((
                model.strings.text(.reviewNextCandidate),
                review.displaySummary ?? review.proposalSection ?? review.candidateId,
                model.strings.text(.topReviewItems),
                .caution,
                { model.openCandidate(review.candidateId) }
            ))
        }

        if let link = model.homeState?.quickLinks.first {
            items.append((
                model.strings.quickLinkLabel(screen: link.screen),
                link.path,
                model.strings.text(.quickLinks),
                .positive,
                { model.openQuickLink(link) }
            ))
        }

        if let daemonAction = model.homeState?.topDaemonActions.first {
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
