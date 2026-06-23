import SwiftUI

struct StateCardView: View {
    let icon: String
    let title: String
    let message: String
    let tone: StatusTone
    let badgeText: String?
    let actionTitle: String?
    let action: (() -> Void)?

    init(
        icon: String,
        title: String,
        message: String,
        tone: StatusTone,
        badgeText: String? = nil,
        actionTitle: String? = nil,
        action: (() -> Void)? = nil
    ) {
        self.icon = icon
        self.title = title
        self.message = message
        self.tone = tone
        self.badgeText = badgeText
        self.actionTitle = actionTitle
        self.action = action
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top, spacing: 12) {
                Label(title, systemImage: icon)
                    .font(.headline)
                    .foregroundStyle(tone.foregroundStyle)
                Spacer()
                if let badgeText, !badgeText.isEmpty {
                    StatusBadge(text: badgeText, tone: tone)
                }
            }
            Text(message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
            if let actionTitle, let action {
                Button(actionTitle, action: action)
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(tone.backgroundStyle, in: RoundedRectangle(cornerRadius: 12))
    }
}
