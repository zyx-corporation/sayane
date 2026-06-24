import SwiftUI

struct ErrorView: View {
    @ObservedObject var model: AppModel
    let message: String

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(model.strings.text(.error)).font(.largeTitle).bold()
            Text(model.strings.text(.connectionProblem))
            SelectableMonospaceText(text: message, font: .body.monospaced())
            BridgeDiagnosticsCard(model: model, compact: true)
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }
}
