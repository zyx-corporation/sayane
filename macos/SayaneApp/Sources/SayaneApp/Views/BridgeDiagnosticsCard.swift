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
                ForEach(model.bridgePrimaryDiagnosticRows(compact: compact)) { row in
                    diagnosticRow(label: row.label, value: row.value)
                }
                if !compact {
                    Divider()
                    routineActionRows
                }
                if !compact, model.shouldExposeDebugCompatibilityTools {
                    Divider()
                    DebugCompatibilityDisclosure(model: model) {
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(model.bridgeDebugDiagnosticRows()) { row in
                                diagnosticRow(label: row.label, value: row.value)
                            }
                            debugActionRows
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

    private var routineActionRows: some View {
        VStack(alignment: .leading, spacing: 8) {
            if model.bridgeNeedsExpandedRecoveryLayout {
                FlowLayout(primaryActionTitles, id: \.self, spacing: 8) { title in
                    actionButton(title) {
                        handleActionTap(title)
                    }
                }
            } else {
                FlowLayout(compactActionTitles, id: \.self, spacing: 8) { title in
                    actionButton(title) {
                        handleActionTap(title)
                    }
                }
            }
        }
    }

    private var debugActionRows: some View {
        FlowLayout(secondaryActionTitles, id: \.self, spacing: 8) { title in
            actionButton(title) {
                handleActionTap(title)
            }
        }
    }

    private var primaryActionTitles: [String] {
        var titles: [String] = []
        if model.launchSourcePath() != nil {
            titles.append(model.strings.text(.openLaunchSource))
        }
        titles.append(model.strings.text(.copyLaunchSource))
        if model.bridgeRecoveryPrefersLauncherAction, model.startupCommandText != nil {
            titles.append(model.strings.text(.openLauncher))
        } else if model.bridgeRecoveryPrefersTokenAction {
            titles.append(model.strings.text(.openToken))
        }
        if !model.bridgeRecoveryPrefersLauncherAction,
           model.bridgeRecoveryShowsLauncherAction,
           model.startupCommandText != nil
        {
            titles.append(model.strings.text(.openLauncher))
        }
        if !model.bridgeRecoveryPrefersTokenAction {
            titles.append(model.strings.text(.openToken))
        }
        titles.append(model.strings.text(.openLogs))
        titles.append(model.strings.text(.copyHealthCommand))
        return Array(NSOrderedSet(array: titles)) as? [String] ?? titles
    }

    private var secondaryActionTitles: [String] {
        [
            model.strings.text(.copyDebugShellURL),
        ]
    }

    private var compactActionTitles: [String] {
        [
            model.strings.text(.copyLaunchSource),
            model.strings.text(.openLogs),
            model.strings.text(.copyHealthCommand),
        ]
    }

    private func handleActionTap(_ title: String) {
        if title == model.strings.text(.openLaunchSource) {
            model.openLaunchSource()
        } else if title == model.strings.text(.copyLaunchSource) {
            model.copyLaunchSource()
        } else if title == model.strings.text(.openLauncher),
                  let startupCommand = model.startupCommandText
        {
            model.openCommandPath(startupCommand)
        } else if title == model.strings.text(.openToken) {
            model.openTokenFile()
        } else if title == model.strings.text(.openLogs) {
            model.openLogFile()
        } else if title == model.strings.text(.copyHealthCommand) {
            model.copyHealthCheckCommand()
        } else if title == model.strings.text(.copyDebugShellURL) {
            model.copyDebugShellURL()
        }
    }

    private func actionButton(_ title: String, action: @escaping () -> Void) -> some View {
        Button(title, action: action)
            .buttonStyle(.bordered)
            .controlSize(compact ? .small : .regular)
    }
}
