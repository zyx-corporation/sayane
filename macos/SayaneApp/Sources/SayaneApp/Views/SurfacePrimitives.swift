import SwiftUI

struct SectionTitle: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.title2)
            .bold()
    }
}

struct SurfaceCard<Content: View>: View {
    let emphasis: Double
    @ViewBuilder let content: Content

    init(
        emphasis: Double = 0.3,
        @ViewBuilder content: () -> Content
    ) {
        self.emphasis = emphasis
        self.content = content()
    }

    var body: some View {
        content
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(.quaternary.opacity(emphasis), in: RoundedRectangle(cornerRadius: 12))
    }
}

struct SheetTitle: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.title2)
            .bold()
    }
}
