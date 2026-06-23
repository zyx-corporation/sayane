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
                    Button(model.strings.text(.openLogs)) {
                        model.openLogFile()
                    }
                    .buttonStyle(.bordered)
                    Button(model.strings.text(.copyHealthCommand)) {
                        model.copyHealthCheckCommand()
                    }
                    .buttonStyle(.bordered)
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
                Task { await model.startBridgeAndReload() }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(compact ? .small : .regular)
        } else if model.bridgeStatusTone == .positive {
            Button(model.strings.text(.refresh)) {
                Task { await model.refreshCurrentScreen() }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(compact ? .small : .regular)
        } else {
            Button(model.strings.text(.bootstrap)) {
                Task { await model.recoverSession() }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(compact ? .small : .regular)
        }
    }
}
