import SwiftUI

struct BridgeStatusPanel: View {
    @ObservedObject var model: AppModel
    let compact: Bool

    init(model: AppModel, compact: Bool = false) {
        self.model = model
        self.compact = compact
    }

    var body: some View {
        SurfaceCard(emphasis: 0.42) {
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .center) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.strings.text(.bridgeStatusPanel))
                            .font(compact ? .headline : .title3)
                            .bold()
                        HStack(spacing: 8) {
                            Text(model.bridgeStatusHeadline)
                                .font(compact ? .subheadline.weight(.semibold) : .headline)
                            if model.bridgeRecoveryInProgress {
                                ProgressView()
                                    .controlSize(compact ? .small : .regular)
                            }
                        }
                        Text(model.bridgeStatusDetail)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    StatusBadge(text: model.bridgeStatusText, tone: model.bridgeStatusTone)
                }

                HStack(spacing: 8) {
                    primaryActionButton
                    if model.bridgeRecoveryPrefersLauncherAction, let startupCommand = model.startupCommandText {
                        Button(model.strings.text(.openLauncher)) {
                            model.openCommandPath(startupCommand)
                        }
                        .buttonStyle(.bordered)
                        .disabled(model.bridgeRecoveryActionDisabled)
                    } else if model.bridgeRecoveryPrefersTokenAction {
                        Button(model.strings.text(.openToken)) {
                            model.openTokenFile()
                        }
                        .buttonStyle(.bordered)
                    }
                    if !compact, model.daemonState != nil {
                        Button(model.strings.text(.daemon)) {
                            model.choose(screen: .daemon)
                        }
                        .buttonStyle(.bordered)
                        .disabled(model.bridgeRecoveryActionDisabled)
                    }
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
                    Button(model.strings.text(.copyHealthCommand)) {
                        model.copyHealthCheckCommand()
                    }
                    .buttonStyle(.bordered)
                    .disabled(model.bridgeRecoveryActionDisabled)
                }

                if let startupCommand = model.startupCommandText {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(model.strings.text(.startupCommand))
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                        CommandRowView(command: startupCommand, lineLimit: compact ? 1 : 2)
                        if !compact {
                            StartupShortcutButtons(model: model, command: startupCommand, controlSize: .small)
                        }
                    }
                }

                if model.currentGateText != nil || model.nextDaemonCommandText != nil || model.nextReadSurfaceText != nil {
                    VStack(alignment: .leading, spacing: 6) {
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
                                CommandRowView(command: nextCommand, lineLimit: compact ? 1 : 2)
                                if let nextReason = model.nextDaemonReasonText, !compact {
                                    Text(nextReason)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        if let nextReadSurface = model.nextReadSurfaceText, !compact {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(model.strings.text(.nextReadSurface))
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(.secondary)
                                CommandRowView(command: nextReadSurface, lineLimit: 2)
                            }
                        }
                    }
                }

                if !compact {
                    Text(model.bridgeStatusPanelSummaryText)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    @ViewBuilder
    private var primaryActionButton: some View {
        Button(model.bridgeSuggestedActionText) {
            Task { await model.performBridgeSuggestedAction() }
        }
        .buttonStyle(.borderedProminent)
        .controlSize(compact ? .small : .regular)
        .disabled(model.bridgeRecoveryActionDisabled)
    }
}
