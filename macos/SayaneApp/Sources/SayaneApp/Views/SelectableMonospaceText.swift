import SwiftUI

struct SelectableMonospaceText: View {
    let text: String
    var font: Font = .system(.body, design: .monospaced)
    var foregroundColor: Color? = nil
    var lineLimit: Int? = nil

    var body: some View {
        Text(text)
            .font(font)
            .textSelection(.enabled)
            .foregroundStyle(foregroundColor ?? .primary)
            .lineLimit(lineLimit)
    }
}
