import SwiftUI

struct DiagnosticsSheetView: View {
    @ObservedObject var model: AppModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    SheetTitle(text: model.strings.text(.troubleshooting))
                    BridgeDiagnosticsCard(model: model, compact: false)
                }
                .padding(24)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(model.strings.text(.close)) {
                        dismiss()
                    }
                }
            }
        }
        .frame(minWidth: 640, minHeight: 520)
    }
}
