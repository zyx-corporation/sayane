import SwiftUI

struct StartupShortcutButtons: View {
    @ObservedObject var model: AppModel
    let command: String
    let controlSize: ControlSize

    init(model: AppModel, command: String, controlSize: ControlSize = .regular) {
        self.model = model
        self.command = command
        self.controlSize = controlSize
    }

    var body: some View {
        HStack {
            if model.resolvedLocalCommandPath(command) != nil {
                Button(model.strings.text(.openLauncher)) {
                    model.openCommandPath(command)
                }
                .buttonStyle(.bordered)
                .controlSize(controlSize)
                .disabled(model.bridgeRecoveryActionDisabled)
            }
            Button(model.strings.text(.copyStartupCommand)) {
                model.copyToClipboard(
                    command,
                    message: model.strings.copiedCommandMessage(context: model.strings.text(.startupCommand))
                )
            }
            .buttonStyle(.bordered)
            .controlSize(controlSize)
        }
    }
}

struct DebugShellShortcutButtons: View {
    @ObservedObject var model: AppModel
    let controlSize: ControlSize

    init(model: AppModel, controlSize: ControlSize = .regular) {
        self.model = model
        self.controlSize = controlSize
    }

    var body: some View {
        HStack {
            Button(model.strings.text(.copyDebugShellURL)) {
                model.copyDebugShellURL()
            }
            .buttonStyle(.bordered)
            .controlSize(controlSize)
        }
    }
}

struct DebugCompatibilityDisclosure<Content: View>: View {
    @ObservedObject var model: AppModel
    let content: () -> Content
    @State private var isExpanded = false

    init(model: AppModel, @ViewBuilder content: @escaping () -> Content) {
        self._model = ObservedObject(wrappedValue: model)
        self.content = content
    }

    var body: some View {
        DisclosureGroup(
            isExpanded: $isExpanded,
            content: {
                VStack(alignment: .leading, spacing: 8) {
                    Text(model.strings.text(.debugCompatibilityToolsSummary))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(model.strings.text(.debugShellCompatibilitySummary))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    content()
                }
                .padding(.top, 4)
            },
            label: {
                Label(
                    isExpanded
                        ? model.strings.text(.hideDebugCompatibilityTools)
                        : model.strings.text(.showDebugCompatibilityTools),
                    systemImage: "ladybug"
                )
                .font(.caption.weight(.semibold))
            }
        )
    }
}
