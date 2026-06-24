import SwiftUI

struct CommandRowView: View {
    let command: String
    var copyLabel: String? = nil
    var font: Font = .system(.body, design: .monospaced)
    var foregroundColor: Color? = nil
    var lineLimit: Int? = nil
    var onCopy: ((String) -> Void)? = nil

    var body: some View {
        HStack(alignment: .top) {
            SelectableMonospaceText(
                text: command,
                font: font,
                foregroundColor: foregroundColor,
                lineLimit: lineLimit
            )
            if let copyLabel, let onCopy {
                Spacer(minLength: 12)
                Button(copyLabel) {
                    onCopy(command)
                }
            }
        }
    }
}
