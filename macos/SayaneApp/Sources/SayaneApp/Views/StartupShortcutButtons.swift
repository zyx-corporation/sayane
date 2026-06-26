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
    let bootstrapUI: String
    let controlSize: ControlSize

    init(model: AppModel, bootstrapUI: String, controlSize: ControlSize = .regular) {
        self.model = model
        self.bootstrapUI = bootstrapUI
        self.controlSize = controlSize
    }

    var body: some View {
        HStack {
            Button(model.strings.text(.openDebugShell)) {
                model.openURLString(bootstrapUI)
            }
            .buttonStyle(.bordered)
            .controlSize(controlSize)
            Button(model.strings.text(.copyDebugShellURL)) {
                model.copyToClipboard(
                    bootstrapUI,
                    message: model.strings.copiedCommandMessage(context: model.strings.text(.debugShell))
                )
            }
            .buttonStyle(.bordered)
            .controlSize(controlSize)
        }
    }
}
