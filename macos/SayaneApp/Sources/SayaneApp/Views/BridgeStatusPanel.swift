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
                        Text(model.bridgeStatusHeadline)
                            .font(compact ? .subheadline.weight(.semibold) : .headline)
                        Text(model.bridgeStatusDetail)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    StatusBadge(text: model.bridgeStatusText, tone: model.bridgeStatusTone)
                }

                HStack(spacing: 8) {
                    primaryActionButton
                    if !compact, model.daemonState != nil {
                        Button(model.strings.text(.daemon)) {
                            model.choose(screen: .daemon)
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
                }

                if let startupCommand = model.startupCommandText {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(model.strings.text(.startupCommand))
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                        CommandRowView(command: startupCommand, lineLimit: compact ? 1 : 2)
                        if !compact {
                            Button(model.strings.text(.copyStartupCommand)) {
                                model.copyStartupCommand()
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
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
                    Text(model.strings.text(.bridgeStatusPanelSummary))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    @ViewBuilder
    private var primaryActionButton: some View {
        if model.health == nil {
            Button(model.strings.text(.startBridge)) {
                Task { await model.performBridgeSuggestedAction() }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(compact ? .small : .regular)
        } else if model.bridgeStatusTone == .positive {
            Button(model.strings.text(.refresh)) {
                Task { await model.performBridgeSuggestedAction() }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(compact ? .small : .regular)
        } else {
            Button(model.strings.text(.bootstrap)) {
                Task { await model.performBridgeSuggestedAction() }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(compact ? .small : .regular)
        }
    }
}
