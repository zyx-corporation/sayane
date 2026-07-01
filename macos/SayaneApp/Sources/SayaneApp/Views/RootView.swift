import SwiftUI

struct RootView: View {
    @ObservedObject var model: AppModel
    @State private var showsDiagnosticsSheet = false

    var body: some View {
        HSplitView {
            sidebar
                .frame(minWidth: 224, idealWidth: 224, maxWidth: 224, alignment: .topLeading)
            detailPane
                .frame(minWidth: 776, idealWidth: 776, maxWidth: .infinity, alignment: .topLeading)
        }
        .toolbar {
            ToolbarItemGroup {
                Button(model.strings.text(.back)) {
                    model.goBack()
                }
                .disabled(!model.canGoBack)
                .keyboardShortcut("[", modifiers: [.command])
                toolbarScreenButton(.home)
                toolbarScreenButton(.queue)
                toolbarScreenButton(.daemon)
            }
            ToolbarItemGroup {
                toolbarClipboardCaptureButton
                    .keyboardShortcut("v", modifiers: [.command, .shift])
                Button(model.toolbarRefreshText) {
                    Task { await model.refreshCurrentScreen() }
                }
                .disabled(model.bridgeRecoveryActionDisabled)
                .keyboardShortcut("r", modifiers: [.command])
                Button(model.strings.text(.openLogs)) {
                    model.openLogFile()
                }
                Button(model.strings.text(.troubleshooting)) {
                    showsDiagnosticsSheet = true
                }
            }
        }
        .sheet(isPresented: $showsDiagnosticsSheet) {
            DiagnosticsSheetView(model: model)
        }
        .task {
            await model.bootstrapAndLoad()
        }
        .onAppear {
            scheduleWindowFit()
        }
        .onChange(of: windowFitSignature) {
            scheduleWindowFit()
        }
        .background(Color(NSColor.controlBackgroundColor).opacity(0.78))
    }

    private var sidebar: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 6) {
                navigationRow(
                    for: .home,
                    systemImage: "house"
                )
                navigationRow(
                    for: .queue,
                    systemImage: "list.bullet.rectangle"
                )
                navigationRow(
                    for: .daemon,
                    systemImage: "bolt.horizontal.circle"
                )
                Spacer(minLength: 0)
            }
            .padding(8)
        }
        .background(Color(NSColor.controlBackgroundColor).opacity(0.42))
    }

    private var detailPane: some View {
        VStack(spacing: 0) {
            workspaceStatusBar
            if model.shouldShowActionFeedbackBanner, let title = model.actionTitle, let message = model.actionMessage {
                FeedbackBanner(
                    title: title,
                    message: message,
                    tone: model.actionTone,
                    showsProgress: model.actionShowsProgress,
                    dismiss: model.dismissActionFeedback
                )
            }
            Group {
                if model.shouldPresentBlockingErrorView, let error = model.errorMessage {
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
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .background(detailBackgroundColor)
    }

    private var detailBackgroundColor: Color {
        Color(NSColor.controlBackgroundColor).opacity(0.78)
    }

    private var windowFitSignature: String {
        [
            "\(model.selectedScreen)",
            model.health?.status ?? "nil",
            model.actionTitle ?? "nil",
            model.actionMessage ?? "nil",
            model.errorMessage ?? "nil",
            model.selectedCandidateID ?? "nil",
            "\(model.queueState?.items.count ?? 0)",
            "\(model.homeState?.topReviewItems.count ?? 0)"
        ].joined(separator: "|")
    }

    private func scheduleWindowFit() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
            WindowSizing.fitAllWindows()
        }
    }

    private var toolbarClipboardCaptureButton: some View {
        Button {
            Task { await model.captureClipboard() }
        } label: {
            Text(model.strings.text(.captureClipboard))
                .font(.caption.weight(.semibold))
                .foregroundStyle(model.clipboardCaptureAvailable ? Color.white : Color.black.opacity(0.85))
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(
                    Capsule()
                        .fill(model.clipboardCaptureAvailable ? Color.blue : Color(NSColor.separatorColor).opacity(0.18))
                )
        }
        .buttonStyle(.plain)
        .disabled(!model.clipboardCaptureAvailable)
    }

    private func toolbarScreenButton(_ screen: AppModel.Screen) -> some View {
        let isSelected = model.selectedScreen == screen
        let title: String = switch screen {
        case .home: model.strings.text(.home)
        case .queue: model.strings.text(.queue)
        case .daemon: model.strings.text(.daemon)
        }

        return Button {
            model.choose(screen: screen)
        } label: {
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(isSelected ? Color.white : Color.primary)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(
                    Capsule()
                        .fill(isSelected ? Color.accentColor : Color(NSColor.quaternaryLabelColor).opacity(0.08))
                )
        }
        .buttonStyle(.plain)
    }

    private var workspaceStatusBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                StatusBadge(text: model.currentScreenTitle, tone: .neutral)
                StatusBadge(text: model.bridgeStatusText, tone: model.bridgeStatusTone)
                if model.isLoading {
                    StatusBadge(text: model.strings.text(.loadingState), tone: .caution)
                }
                Text(model.currentScreenSummary)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                if model.shouldShowNavigationTrailInStatusBar {
                    Divider().frame(height: 16)
                    StatusBadge(text: model.navigationTrailText, tone: .neutral)
                }
                if model.shouldShowSelectedCandidateInStatusBar,
                   let selectedCandidate = model.selectedCandidateBadgeText
                {
                    Divider().frame(height: 16)
                    StatusBadge(text: selectedCandidate, tone: .caution)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
        }
        .background(.quaternary.opacity(0.35))
    }

    private func navigationRow(for screen: AppModel.Screen, systemImage: String) -> some View {
        let metadata = model.sidebarMetadata(for: screen)
        let isSelected = model.selectedScreen == screen
        return Button {
            model.choose(screen: screen)
        } label: {
            HStack(alignment: .center, spacing: 8) {
                Image(systemName: systemImage)
                    .foregroundStyle(.secondary)
                VStack(alignment: .leading, spacing: 1) {
                    Text(metadata.title)
                    if isSelected {
                        Text(metadata.summary)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                }
                Spacer(minLength: 8)
                if let badgeText = metadata.badgeText, !badgeText.isEmpty {
                    StatusBadge(text: badgeText, tone: metadata.badgeTone)
                }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(isSelected ? Color.accentColor.opacity(0.12) : Color.clear)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(isSelected ? Color.accentColor.opacity(0.35) : Color.clear, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(.plain)
    }
}
