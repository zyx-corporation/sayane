import SwiftUI

struct HomeView: View {
    @ObservedObject var model: AppModel
    @State private var showsDiagnosticsSheet = false
    @State private var showsStatusDetails = false
    private let launcherCardHeight: CGFloat = 126

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            header
            homeStatusLauncherBar
            launcherSection
            VStack(alignment: .leading, spacing: 12) {
                minimalLinksRow
                if showsBridgeDiagnostics {
                    diagnosticsPromptCard
                }
            }
            Spacer(minLength: 0)
        }
        .padding(18)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color(NSColor.underPageBackgroundColor))
        .navigationTitle(model.strings.text(.home))
        .sheet(isPresented: $showsDiagnosticsSheet) {
            DiagnosticsSheetView(model: model)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .center, spacing: 10) {
                VStack(alignment: .leading, spacing: 6) {
                    Text(model.strings.text(.appTitle))
                        .font(.title2)
                        .bold()
                    Text(model.homeBridgeSummaryText)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
            }
        }
    }

    private var homeStatusLauncherBar: some View {
        SurfaceCard(emphasis: 0.22) {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 6) {
                    statusChip(
                        title: model.strings.text(.backend),
                        value: model.bridgeStatusText,
                        tone: model.bridgeStatusTone
                    )
                    statusChip(
                        title: "Vault",
                        value: vaultStatusText,
                        tone: vaultStatusTone
                    )
                    statusChip(
                        title: "Queue",
                        value: queueCountText,
                        tone: queueCountTone
                    )
                    Spacer()
                    Button(showsStatusDetails ? "閉じる" : "詳細 ›") {
                        withAnimation(.easeInOut(duration: 0.16)) {
                            showsStatusDetails.toggle()
                        }
                    }
                    .buttonStyle(.plain)
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.secondary)
                }

                if showsStatusDetails {
                    VStack(alignment: .leading, spacing: 6) {
                        statusDetailRow(
                            title: model.strings.text(.backend),
                            summary: model.bridgeStatusDetail,
                            tone: model.bridgeStatusTone
                        )
                        statusDetailRow(
                            title: "Vault",
                            summary: vaultStatusDetailText,
                            tone: vaultStatusTone
                        )
                        statusDetailRow(
                            title: "Queue",
                            summary: queueStatusDetailText,
                            tone: queueCountTone
                        )
                    }
                    .transition(.opacity.combined(with: .move(edge: .top)))
                }
            }
        }
    }

    private var launcherSection: some View {
        HStack(alignment: .top, spacing: 10) {
            reviewLauncherCard
                .frame(maxWidth: .infinity, minHeight: launcherCardHeight, maxHeight: launcherCardHeight, alignment: .topLeading)
            daemonLauncherCard
                .frame(maxWidth: .infinity, minHeight: launcherCardHeight, maxHeight: launcherCardHeight, alignment: .topLeading)
        }
    }

    private var reviewLauncherCard: some View {
        Group {
            if let review = model.homeState?.topReviewItems.first {
                launcherCard(
                    eyebrow: "次のレビュー対象",
                    badgeText: reviewPriorityBadge(review),
                    badgeTone: reviewPriorityTone(review),
                    title: "\(review.candidateId) / \(homeReviewItemSummary(review))",
                    summary: reviewCardSummary(review),
                    primaryTitle: model.strings.text(.reviewNextCandidate),
                    primaryTone: .positive,
                    primaryAction: { model.openCandidate(review.candidateId) },
                    secondaryTitle: "スキップ",
                    secondaryAction: nil
                )
            } else {
                launcherCard(
                    eyebrow: "次のレビュー対象",
                    badgeText: model.homePriorityEmptyBadgeText,
                    badgeTone: .neutral,
                    title: model.strings.text(.reviewNextCandidate),
                    summary: model.homePriorityEmptyMessage,
                    primaryTitle: model.toolbarRefreshText,
                    primaryTone: .neutral,
                    primaryAction: { Task { await model.refreshCurrentScreen() } },
                    secondaryTitle: nil,
                    secondaryAction: nil
                )
            }
        }
    }

    private var daemonLauncherCard: some View {
        Group {
            if let action = effectiveHomeDaemonAction {
                launcherCard(
                    eyebrow: "次のバックエンドアクション",
                    badgeText: homeDaemonActionTitle(action),
                    badgeTone: homeDaemonActionTone(action),
                    title: model.currentGateText ?? model.bridgeStatusHeadline,
                    summary: homeDaemonActionSummary(action),
                    primaryTitle: model.bridgeSuggestedActionText,
                    primaryTone: .caution,
                    primaryAction: { Task { await model.performBridgeSuggestedAction() } },
                    secondaryTitle: model.strings.text(.daemon),
                    secondaryAction: { model.choose(screen: .daemon) }
                )
            } else {
                launcherCard(
                    eyebrow: "次のバックエンドアクション",
                    badgeText: model.bridgeStatusText,
                    badgeTone: model.bridgeStatusTone,
                    title: model.currentGateText ?? model.bridgeStatusHeadline,
                    summary: model.strings.text(.noDaemonActions),
                    primaryTitle: model.strings.text(.daemon),
                    primaryTone: .neutral,
                    primaryAction: { model.choose(screen: .daemon) },
                    secondaryTitle: nil,
                    secondaryAction: nil
                )
            }
        }
    }

    private func launcherCard(
        eyebrow: String,
        badgeText: String,
        badgeTone: StatusTone,
        title: String,
        summary: String,
        primaryTitle: String,
        primaryTone: StatusTone,
        primaryAction: @escaping () -> Void,
        secondaryTitle: String?,
        secondaryAction: (() -> Void)?
    ) -> some View {
        SurfaceCard(emphasis: 0.28) {
            VStack(alignment: .leading, spacing: 8) {
                Text(eyebrow)
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(.secondary)
                HStack(alignment: .top, spacing: 8) {
                    StatusBadge(text: badgeText, tone: badgeTone)
                    Text(title)
                        .font(.subheadline.weight(.semibold))
                    Spacer()
                }
                Text(summary)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
                HStack(spacing: 8) {
                    Button(primaryTitle, action: primaryAction)
                        .buttonStyle(.borderedProminent)
                        .controlSize(.small)
                        .disabled(model.bridgeRecoveryActionDisabled && primaryTitle != model.strings.text(.reviewNextCandidate))
                    if let secondaryTitle, let secondaryAction {
                        Button(secondaryTitle, action: secondaryAction)
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                    } else if let secondaryTitle {
                        Text(secondaryTitle)
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
    }

    private var minimalLinksRow: some View {
        HStack(spacing: 12) {
            Button(model.strings.text(.queue)) {
                model.choose(screen: .queue)
            }
            .buttonStyle(.plain)
            Button(model.strings.text(.daemon)) {
                model.choose(screen: .daemon)
            }
            .buttonStyle(.plain)
            Spacer()
            Button(model.strings.text(.troubleshooting)) {
                showsDiagnosticsSheet = true
            }
            .buttonStyle(.plain)
            .foregroundStyle(.secondary)
        }
        .font(.caption.weight(.semibold))
        .padding(.top, 2)
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
    private func statusChip(title: String, value: String, tone: StatusTone) -> some View {
        HStack(spacing: 6) {
            Circle()
                .fill(tone.foregroundStyle)
                .frame(width: 7, height: 7)
            Text(title)
                .font(.caption2.weight(.semibold))
            if !value.isEmpty {
                Text(value)
                    .font(.caption2.weight(.semibold))
            }
        }
        .foregroundStyle(.primary)
        .padding(.horizontal, 7)
        .padding(.vertical, 5)
        .background(Color(NSColor.windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.secondary.opacity(0.15), lineWidth: 1)
        )
    }

    private func statusDetailRow(title: String, summary: String, tone: StatusTone) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Circle()
                .fill(tone.foregroundStyle)
                .frame(width: 8, height: 8)
                .padding(.top, 4)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption2.weight(.semibold))
                Text(summary)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func reviewPriorityBadge(_ item: TopReviewItem) -> String {
        item.requiresReview == true
            ? model.strings.text(.recommended)
            : (item.status.map(model.strings.statusValueLabel) ?? model.strings.text(.topReviewItems))
    }

    private func reviewPriorityTone(_ item: TopReviewItem) -> StatusTone {
        item.status.map(model.strings.tone(forToken:)) ?? .caution
    }

    private func reviewCardSummary(_ item: TopReviewItem) -> String {
        item.displaySummary
            ?? item.proposalSection.map(model.strings.residentValueLabel)
            ?? model.strings.text(.none)
    }

    private func homeReviewItemSummary(_ item: TopReviewItem) -> String {
        item.displaySummary
            ?? item.proposalSection.map(model.strings.residentValueLabel)
            ?? item.status.map(model.strings.statusValueLabel)
            ?? model.strings.text(.none)
    }

    private var queueCountText: String {
        let count = model.queueState?.reviewableCount ?? model.homeState?.topReviewItems.count ?? 0
        return "\(count)"
    }

    private var queueCountTone: StatusTone {
        (model.queueState?.reviewableCount ?? 0) > 0 ? .caution : .positive
    }

    private var queueStatusDetailText: String {
        let reviewable = model.queueState?.reviewableCount ?? 0
        let total = model.queueState?.items.count ?? 0
        return "\(total) 件中 \(reviewable) 件がレビュー待ちです"
    }

    private var vaultStatusText: String {
        guard let summary = model.homeState?.vaultSummary else {
            return model.strings.text(.none)
        }
        return model.strings.summaryValueLabel(key: "vault_status", value: summary.status ?? "unavailable")
    }

    private var vaultStatusTone: StatusTone {
        guard let status = model.homeState?.vaultSummary?.status else { return .neutral }
        return model.strings.tone(forToken: status)
    }

    private var vaultStatusDetailText: String {
        guard let summary = model.homeState?.vaultSummary else {
            return model.strings.text(.vaultUnavailable)
        }
        if let sessionStatus = summary.sessionStatus {
            return "\(summary.backend ?? "-") · active \(sessionStatus.activeSessionCount)"
        }
        return "\(summary.backend ?? "-") · \(summary.status ?? "-")"
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

    private var effectiveHomeDaemonAction: String? {
        model.nextDaemonCommandText ?? model.homeState?.topDaemonActions.first
    }

    private var showsBridgeDiagnostics: Bool {
        if model.errorMessage != nil { return true }
        guard let status = model.health?.status.lowercased() else { return true }
        return status != "ok" && status != "healthy"
    }
}
