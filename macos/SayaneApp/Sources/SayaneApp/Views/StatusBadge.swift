import SwiftUI

enum StatusTone: Equatable {
    case neutral
    case positive
    case caution
    case critical

    var foregroundStyle: Color {
        switch self {
        case .neutral: return .secondary
        case .positive: return .green
        case .caution: return .orange
        case .critical: return .red
        }
    }

    var backgroundStyle: Color {
        switch self {
        case .neutral: return .gray.opacity(0.14)
        case .positive: return .green.opacity(0.14)
        case .caution: return .orange.opacity(0.14)
        case .critical: return .red.opacity(0.14)
        }
    }

    var symbolName: String {
        switch self {
        case .neutral: return "circle"
        case .positive: return "checkmark.circle.fill"
        case .caution: return "exclamationmark.triangle.fill"
        case .critical: return "xmark.octagon.fill"
        }
    }
}

struct StatusBadge: View {
    let text: String
    let tone: StatusTone

    var body: some View {
        Label(text, systemImage: tone.symbolName)
            .font(.caption.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .foregroundStyle(tone.foregroundStyle)
            .background(tone.backgroundStyle, in: Capsule())
    }
}
