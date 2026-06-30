import SwiftUI

struct FeedbackBanner: View {
    let title: String
    let message: String
    let tone: StatusTone
    let showsProgress: Bool
    let dismiss: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 8) {
                    StatusBadge(text: title, tone: tone)
                    if showsProgress {
                        ProgressView()
                            .controlSize(.small)
                    }
                }
            }
            Text(message)
                .font(.subheadline)
                .frame(maxWidth: .infinity, alignment: .leading)
            Button(action: dismiss) {
                Image(systemName: "xmark")
            }
            .buttonStyle(.plain)
            .accessibilityLabel(title)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(tone.backgroundStyle, in: RoundedRectangle(cornerRadius: 12))
        .padding(.horizontal, 14)
        .padding(.top, 8)
    }
}
