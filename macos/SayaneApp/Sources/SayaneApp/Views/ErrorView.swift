import SwiftUI

struct ErrorView: View {
    @ObservedObject var model: AppModel
    let message: String

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(model.strings.text(.error)).font(.largeTitle).bold()
            Text(model.strings.text(.connectionProblem))
            compactRecoveryCard
            SelectableMonospaceText(text: message, font: .body.monospaced())
            BridgeDiagnosticsCard(model: model, compact: true)
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }

    @ViewBuilder
    private var compactRecoveryCard: some View {
        SurfaceCard(emphasis: 0.42) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.bridgeSuggestedActionText)
                    .font(.headline)
                Text(model.strings.text(.sessionProblem))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                if let startupCommand = model.startupCommandText {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.strings.text(.startupCommand))
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                        CommandRowView(command: startupCommand, lineLimit: 2)
                        StartupShortcutButtons(model: model, command: startupCommand)
                    }
                }
                if let bootstrapUI = model.daemonState?.operatorPhaseDetails.currentSupportedOperatorPath.bootstrapUI {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.strings.text(.bootstrapUI))
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                        CommandRowView(command: bootstrapUI, lineLimit: 2)
                        DebugShellShortcutButtons(model: model, bootstrapUI: bootstrapUI)
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
                HStack(spacing: 8) {
                    Button(model.bridgeSuggestedActionText) {
                        Task { await model.performBridgeSuggestedAction() }
                    }
                    .buttonStyle(.borderedProminent)
                    Button(model.strings.text(.openLogs)) {
                        model.openLogFile()
                    }
                    .buttonStyle(.bordered)
                }
            }
        }
    }
}
