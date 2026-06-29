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
                ForEach(model.bridgeDiagnosticRows(compact: compact)) { row in
                    diagnosticRow(label: row.label, value: row.value)
                }
                if !compact {
                    Divider()
                    DebugCompatibilityDisclosure(model: model) {
                        VStack(alignment: .leading, spacing: 8) {
                            actionRows
                        }
                    }
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
            if model.bridgeNeedsExpandedRecoveryLayout {
                HStack {
                    if model.launchSourcePath() != nil {
                        actionButton(model.strings.text(.openLaunchSource)) {
                            model.openLaunchSource()
                        }
                    }
                    actionButton(model.strings.text(.copyLaunchSource)) {
                        model.copyLaunchSource()
                    }
                    if model.bridgeRecoveryPrefersLauncherAction, let startupCommand = model.startupCommandText {
                        actionButton(model.strings.text(.openLauncher)) {
                            model.openCommandPath(startupCommand)
                        }
                    } else if model.bridgeRecoveryPrefersTokenAction {
                        actionButton(model.strings.text(.openToken)) {
                            model.openTokenFile()
                        }
                    }
                    if !model.bridgeRecoveryPrefersLauncherAction,
                       model.bridgeRecoveryShowsLauncherAction,
                       let startupCommand = model.startupCommandText
                    {
                        actionButton(model.strings.text(.openLauncher)) {
                            model.openCommandPath(startupCommand)
                        }
                    }
                    if !model.bridgeRecoveryPrefersTokenAction {
                        actionButton(model.strings.text(.openToken)) {
                            model.openTokenFile()
                        }
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
            } else {
                FlowLayout([
                    model.strings.text(.copyLaunchSource),
                    model.strings.text(.openLogs),
                    model.strings.text(.copyHealthCommand),
                    model.strings.text(.openDebugShell),
                    model.strings.text(.copyDebugShellURL),
                ], id: \.self, spacing: 8) { title in
                    actionButton(title) {
                        if title == model.strings.text(.copyLaunchSource) {
                            model.copyLaunchSource()
                        } else if title == model.strings.text(.openLogs) {
                            model.openLogFile()
                        } else if title == model.strings.text(.copyHealthCommand) {
                            model.copyHealthCheckCommand()
                        } else if title == model.strings.text(.openDebugShell) {
                            model.openDebugShell()
                        } else {
                            model.copyDebugShellURL()
                        }
                    }
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
