import SwiftUI

struct BridgeDiagnosticsCard: View {
    @ObservedObject var model: AppModel
    let compact: Bool

    var body: some View {
        SurfaceCard(emphasis: 0.35) {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    SectionTitle(text: model.strings.text(.connectionDiagnostics))
                    Spacer()
                    StatusBadge(text: model.bridgeStatusText, tone: model.bridgeStatusTone)
                }
                diagnosticRow(label: model.strings.text(.bridgeURL), value: model.bridgeBaseURLText)
                diagnosticRow(label: model.strings.text(.healthEndpoint), value: model.bridgeHealthURLText)
                diagnosticRow(label: model.strings.text(.tokenFile), value: model.bridgeTokenFilePath)
                diagnosticRow(label: model.strings.text(.logFile), value: model.bridgeLogFilePath)
                diagnosticRow(label: model.strings.text(.profile), value: model.bridgeProfileID)
                if !compact {
                    Divider()
                    diagnosticRow(label: model.strings.text(.debugShell), value: model.bridgeDebugShellURLText)
                    Text(model.strings.text(.debugShellCompatibilitySummary))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    actionRows
                }
            }
        }
    }

    @ViewBuilder
    private func diagnosticRow(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
            SelectableMonospaceText(text: value, font: .system(.caption, design: .monospaced))
        }
    }

    private var actionRows: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                actionButton(model.strings.text(.openToken)) {
                    model.openTokenFile()
                }
                actionButton(model.strings.text(.openLogs)) {
                    model.openLogFile()
                }
                actionButton(model.strings.text(.copyHealthCommand)) {
                    model.copyHealthCheckCommand()
                }
            }
            HStack {
                actionButton(model.strings.text(.openDebugShell)) {
                    model.openDebugShell()
                }
                actionButton(model.strings.text(.copyDebugShellURL)) {
                    model.copyDebugShellURL()
                }
            }
        }
    }

    private func actionButton(_ title: String, action: @escaping () -> Void) -> some View {
        Button(title, action: action)
            .buttonStyle(.bordered)
            .controlSize(compact ? .small : .regular)
    }
}
