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
            .background(Color(NSColor.windowBackgroundColor), in: RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.primary.opacity(0.16 + emphasis * 0.12), lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.03 + emphasis * 0.04), radius: 4, y: 1)
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
