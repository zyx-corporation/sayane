import SwiftUI

struct ErrorView: View {
    private enum RecoveryButtonKind {
        case prominent
        case regular
    }

    @ObservedObject var model: AppModel
    let message: String
    @State private var showsRawError = false
    @State private var showsDiagnosticsSheet = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(model.strings.text(.error)).font(.largeTitle).bold()
            issueSummaryCard
            compactRecoveryCard
            rawErrorDisclosure
            diagnosticsPromptCard
        }
        .padding(24)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .sheet(isPresented: $showsDiagnosticsSheet) {
            DiagnosticsSheetView(model: model)
        }
    }

    @ViewBuilder
    private var compactRecoveryCard: some View {
        SurfaceCard(emphasis: 0.42) {
            VStack(alignment: .leading, spacing: 10) {
                HStack(spacing: 8) {
                    Text(model.bridgeSuggestedActionText)
                        .font(.headline)
                    if model.bridgeRecoveryInProgress {
                        ProgressView()
                            .controlSize(.small)
                    }
                }
                Text(model.errorDisplayMessage ?? model.strings.text(.sessionProblem))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                recoveryHints
                if let startupCommand = model.startupCommandText {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.strings.text(.startupCommand))
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                        CommandRowView(command: startupCommand, lineLimit: 2)
                        StartupShortcutButtons(model: model, command: startupCommand)
                    }
                }
                if let currentGate = model.currentGateText {
                    HStack(alignment: .top, spacing: 8) {
                        Text(model.strings.text(.currentGate))
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                        Text(currentGate)
                            .font(.caption)
                    }
                }
                if let nextCommand = model.nextDaemonCommandText {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.strings.text(.nextCommand))
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                        CommandRowView(command: nextCommand, lineLimit: 2)
                    }
                }
                recoveryActionRows
            }
        }
    }

    private var issueSummaryCard: some View {
        SurfaceCard(emphasis: 0.22) {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    StatusBadge(text: model.strings.text(.needsAttention), tone: .critical)
                    Text(model.bridgeRecoveryIssueTitle)
                        .font(.headline)
                }
                Text(model.bridgeRecoveryIssueSummary)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var rawErrorDisclosure: some View {
        DisclosureGroup(
            isExpanded: $showsRawError,
            content: {
                VStack(alignment: .leading, spacing: 6) {
                    Text(model.strings.text(.errorDetails))
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    SelectableMonospaceText(text: message, font: .body.monospaced())
                }
                .padding(.top, 4)
            },
            label: {
                Label(
                    showsRawError
                        ? model.strings.text(.hideErrorDetails)
                        : model.strings.text(.showErrorDetails),
                    systemImage: "exclamationmark.bubble"
                )
                .font(.caption.weight(.semibold))
            }
        )
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

    private var recoveryActionRows: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                if model.bridgeRecoveryPrefersLauncherAction, let startupCommand = model.startupCommandText {
                    Button(model.strings.text(.openLauncher)) {
                        model.openCommandPath(startupCommand)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(model.bridgeRecoveryActionDisabled)
                } else if model.bridgeRecoveryPrefersTokenAction {
                    Button(model.strings.text(.openToken)) {
                        model.openTokenFile()
                    }
                    .buttonStyle(.borderedProminent)
                } else {
                    primaryRecoveryButton(kind: .prominent)
                }

                if model.bridgeRecoveryPrefersLauncherAction || model.bridgeRecoveryPrefersTokenAction {
                    primaryRecoveryButton(kind: .regular)
                }
                if !model.bridgeNeedsExpandedRecoveryLayout {
                    Button(model.strings.text(.openLogs)) {
                        model.openLogFile()
                    }
                    .buttonStyle(.bordered)
                }
            }

                if model.bridgeNeedsExpandedRecoveryLayout {
                    HStack(spacing: 8) {
                        if model.launchSourcePath() != nil {
                            Button(model.strings.text(.openLaunchSource)) {
                                model.openLaunchSource()
                            }
                            .buttonStyle(.bordered)
                        }
                        Button(model.strings.text(.copyLaunchSource)) {
                            model.copyLaunchSource()
                        }
                        .buttonStyle(.bordered)
                        if !model.bridgeRecoveryPrefersLauncherAction,
                           model.bridgeRecoveryShowsLauncherAction,
                           let startupCommand = model.startupCommandText
                        {
                            Button(model.strings.text(.openLauncher)) {
                            model.openCommandPath(startupCommand)
                        }
                        .buttonStyle(.bordered)
                        .disabled(model.bridgeRecoveryActionDisabled)
                    }
                    if !model.bridgeRecoveryPrefersTokenAction, model.bridgeRecoveryShowsTokenAction {
                        Button(model.strings.text(.openToken)) {
                            model.openTokenFile()
                        }
                        .buttonStyle(.bordered)
                    }
                    Button(model.strings.text(.openLogs)) {
                        model.openLogFile()
                    }
                    .buttonStyle(.bordered)
                }
            }
        }
    }

    @ViewBuilder
    private func primaryRecoveryButton(kind: RecoveryButtonKind) -> some View {
        switch kind {
        case .prominent:
            Button(model.bridgeSuggestedActionText) {
                Task { await model.performBridgeSuggestedAction() }
            }
            .buttonStyle(.borderedProminent)
            .disabled(model.bridgeRecoveryActionDisabled)
        case .regular:
            Button(model.bridgeSuggestedActionText) {
                Task { await model.performBridgeSuggestedAction() }
            }
            .buttonStyle(.bordered)
            .disabled(model.bridgeRecoveryActionDisabled)
        }
    }

    private var recoveryHints: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(model.bridgeRecoveryHintTitle)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            ForEach(Array(model.bridgeRecoveryStepMessages.enumerated()), id: \.offset) { _, step in
                HStack(alignment: .top, spacing: 8) {
                    Text("•")
                    Text(step)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
}
