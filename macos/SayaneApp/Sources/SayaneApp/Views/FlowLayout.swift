import SwiftUI

struct FlowLayout<Data: RandomAccessCollection, ID: Hashable, Content: View>: View {
    let data: Data
    let id: KeyPath<Data.Element, ID>
    let spacing: CGFloat
    @ViewBuilder let content: (Data.Element) -> Content

    init(
        _ data: Data,
        id: KeyPath<Data.Element, ID>,
        spacing: CGFloat = 8,
        @ViewBuilder content: @escaping (Data.Element) -> Content
    ) {
        self.data = data
        self.id = id
        self.spacing = spacing
        self.content = content
    }

    var body: some View {
        WrappingFlowLayout(spacing: spacing) {
            ForEach(Array(data), id: id) { element in
                content(element)
            }
        }
    }
}

private struct WrappingFlowLayout: Layout {
    let spacing: CGFloat

    init(spacing: CGFloat = 8) {
        self.spacing = spacing
    }

    func sizeThatFits(
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) -> CGSize {
        let rows = rows(for: proposal, subviews: subviews)
        let width = rows.map(\.width).max() ?? 0
        let height = rows.last.map { $0.yOffset + $0.height } ?? 0
        return CGSize(width: width, height: height)
    }

    func placeSubviews(
        in bounds: CGRect,
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) {
        let rows = rows(for: proposal, subviews: subviews)
        for row in rows {
            for element in row.elements {
                let point = CGPoint(
                    x: bounds.minX + element.origin.x,
                    y: bounds.minY + element.origin.y
                )
                subviews[element.index].place(
                    at: point,
                    proposal: ProposedViewSize(element.size)
                )
            }
        }
    }

    private func rows(
        for proposal: ProposedViewSize,
        subviews: Subviews
    ) -> [Row] {
        let maxWidth = proposal.width ?? .greatestFiniteMagnitude
        var rows: [Row] = []
        var current = Row(yOffset: 0)

        for index in subviews.indices {
            let size = subviews[index].sizeThatFits(.unspecified)
            let nextX = current.elements.isEmpty ? 0 : current.width + spacing
            let exceedsWidth = nextX + size.width > maxWidth

            if exceedsWidth, !current.elements.isEmpty {
                rows.append(current)
                current = Row(yOffset: current.yOffset + current.height + spacing)
            }

            let originX = current.elements.isEmpty ? 0 : current.width + spacing
            let origin = CGPoint(x: originX, y: current.yOffset)
            current.elements.append(RowElement(index: index, size: size, origin: origin))
            current.width = originX + size.width
            current.height = max(current.height, size.height)
        }

        if !current.elements.isEmpty {
            rows.append(current)
        }

        return rows
    }

    private struct Row {
        var elements: [RowElement] = []
        var width: CGFloat = 0
        var height: CGFloat = 0
        let yOffset: CGFloat
    }

    private struct RowElement {
        let index: Int
        let size: CGSize
        let origin: CGPoint
    }
}
