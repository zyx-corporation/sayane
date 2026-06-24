import SwiftUI

struct DetailBadgeRow: View {
    let label: String
    let badgeText: String
    let tone: StatusTone

    var body: some View {
        HStack {
            Text("\(label):")
            StatusBadge(text: badgeText, tone: tone)
        }
    }
}
