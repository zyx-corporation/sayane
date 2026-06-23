import SwiftUI

struct RootView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        NavigationSplitView {
            List(selection: Binding(
                get: { model.selectedScreen },
                set: { if let value = $0 { model.choose(screen: value) } }
            )) {
                navigationRow(
                    for: .home,
                    systemImage: "house"
                )
                .tag(AppModel.Screen.home)
                navigationRow(
                    for: .queue,
                    systemImage: "list.bullet.rectangle"
                )
                .tag(AppModel.Screen.queue)
                navigationRow(
                    for: .daemon,
                    systemImage: "bolt.horizontal.circle"
                )
                .tag(AppModel.Screen.daemon)
            }
            .navigationTitle(model.strings.text(.appTitle))
        } detail: {
            VStack(spacing: 0) {
                workspaceStatusBar
                if let title = model.actionTitle, let message = model.actionMessage {
                    FeedbackBanner(
                        title: title,
                        message: message,
                        tone: model.actionTone,
                        dismiss: model.dismissActionFeedback
                    )
                }
                Group {
                    if let error = model.errorMessage {
                        ErrorView(model: model, message: error)
                    } else {
                        switch model.selectedScreen {
                        case .home:
                            HomeView(model: model)
                        case .queue:
                            QueueAndDetailView(model: model)
                        case .daemon:
                            DaemonView(model: model)
                        }
                    }
                }
            }
            .toolbar {
                ToolbarItemGroup {
                    Button(model.strings.text(.back)) {
                        model.goBack()
                    }
                    .disabled(!model.canGoBack)
                    .keyboardShortcut("[", modifiers: [.command])
                    Button(model.strings.text(.home)) {
                        model.choose(screen: .home)
                    }
                    Button(model.strings.text(.queue)) {
                        model.choose(screen: .queue)
                    }
                    Button(model.strings.text(.daemon)) {
                        model.choose(screen: .daemon)
                    }
                }
                ToolbarItemGroup {
                    Button(model.strings.text(.captureClipboard)) {
                        Task { await model.captureClipboard() }
                    }
                    .keyboardShortcut("v", modifiers: [.command, .shift])
                    Button(model.strings.text(.refresh)) {
                        Task { await model.refreshCurrentScreen() }
                    }
                    .keyboardShortcut("r", modifiers: [.command])
                    Button(model.strings.text(.openLogs)) {
                        model.openLogFile()
                    }
                }
            }
        }
        .task {
            await model.bootstrapAndLoad()
        }
    }

    private var workspaceStatusBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                StatusBadge(
                    text: "\(model.strings.text(.screenOverview)): \(model.currentScreenTitle)",
                    tone: .neutral
                )
                StatusBadge(text: model.bridgeStatusText, tone: model.bridgeStatusTone)
                if model.isLoading {
                    StatusBadge(text: model.strings.text(.loadingState), tone: .caution)
                }
                Text(model.currentScreenSummary)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Divider().frame(height: 16)
                Text("\(model.strings.text(.navigationTrail)): \(model.navigationTrailText)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                if let selectedCandidate = model.selectedCandidateBadgeText {
                    Divider().frame(height: 16)
                    Text(selectedCandidate)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .background(.quaternary.opacity(0.35))
    }

    private func navigationRow(for screen: AppModel.Screen, systemImage: String) -> some View {
        let metadata = model.sidebarMetadata(for: screen)
        return HStack(alignment: .center, spacing: 8) {
            Image(systemName: systemImage)
                .foregroundStyle(.secondary)
            VStack(alignment: .leading, spacing: 2) {
                Text(metadata.title)
                Text(metadata.summary)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
            Spacer(minLength: 8)
            if let badgeText = metadata.badgeText, !badgeText.isEmpty {
                StatusBadge(text: badgeText, tone: metadata.badgeTone)
            }
        }
    }
}
