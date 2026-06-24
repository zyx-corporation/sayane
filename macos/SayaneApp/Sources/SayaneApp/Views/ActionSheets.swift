import SwiftUI

struct EvaluateSheet: View {
    @ObservedObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @State private var level = 1

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            SheetTitle(text: model.strings.text(.evaluate))
            Picker(model.strings.text(.evaluateLevel), selection: $level) {
                Text(model.strings.evaluationLevelLabel(1, detailed: true)).tag(1)
                Text(model.strings.evaluationLevelLabel(2, detailed: true)).tag(2)
                Text(model.strings.evaluationLevelLabel(3, detailed: true)).tag(3)
            }
            .pickerStyle(.menu)
            HStack {
                Button(model.strings.text(.cancel)) { dismiss() }
                Button(model.strings.text(.submit)) {
                    Task {
                        if await model.evaluateSelected(level: level) {
                            dismiss()
                        }
                    }
                }
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding(24)
        .frame(width: 420)
    }
}

struct RejectSheet: View {
    @ObservedObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @State private var reason = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            SheetTitle(text: model.strings.text(.reject))
            TextField(model.strings.text(.rejectReason), text: $reason)
            HStack {
                Button(model.strings.text(.cancel)) { dismiss() }
                Button(model.strings.text(.submit)) {
                    Task {
                        if await model.rejectSelected(reason: reason.isEmpty ? nil : reason) {
                            dismiss()
                        }
                    }
                }
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding(24)
        .frame(width: 420)
    }
}

struct ReviseSheet: View {
    @ObservedObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @State private var editedText = ""
    @State private var targetSection = ""
    @State private var changeReason = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            SheetTitle(text: model.strings.text(.revise))
            TextField(model.strings.text(.targetSection), text: $targetSection)
            TextField(model.strings.text(.changeReason), text: $changeReason)
            TextEditor(text: $editedText)
                .frame(minHeight: 180)
                .border(.quaternary)
            HStack {
                Button(model.strings.text(.cancel)) { dismiss() }
                Button(model.strings.text(.submit)) {
                    Task {
                        if await model.reviseSelected(
                            editedText: editedText,
                            targetSection: targetSection.isEmpty ? nil : targetSection,
                            changeReason: changeReason.isEmpty ? nil : changeReason
                        ) {
                            dismiss()
                        }
                    }
                }
                .keyboardShortcut(.defaultAction)
                .disabled(editedText.isEmpty)
            }
        }
        .padding(24)
        .frame(width: 560, height: 420)
        .onAppear {
            if editedText.isEmpty {
                editedText = model.detailState?.content ?? ""
                targetSection = model.detailState?.uiSummary.section ?? ""
            }
        }
    }
}
