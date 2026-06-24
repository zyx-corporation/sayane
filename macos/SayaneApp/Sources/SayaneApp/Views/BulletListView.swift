import SwiftUI

struct BulletListView: View {
    let values: [String]

    var body: some View {
        ForEach(values, id: \.self) { value in
            Text("• \(value)")
        }
    }
}

struct TitledBulletListView: View {
    let title: String
    let values: [String]

    var body: some View {
        if !values.isEmpty {
            VStack(alignment: .leading, spacing: 4) {
                Text(title).bold()
                BulletListView(values: values)
            }
        }
    }
}
