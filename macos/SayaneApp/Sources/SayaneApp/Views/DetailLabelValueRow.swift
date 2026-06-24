import SwiftUI

struct DetailLabelValueRow: View {
    let label: String
    let value: String

    var body: some View {
        Text("\(label): \(value)")
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}
