import SwiftUI

struct SummaryCardValueView: View {
    let strings: AppStrings
    let card: SummaryCard

    var body: some View {
        if let string = card.value?.stringValue {
            StatusBadge(
                text: strings.summaryValueLabel(key: card.key, value: string),
                tone: strings.tone(forToken: string)
            )
        } else if let boolValue = card.value?.boolValue {
            StatusBadge(
                text: strings.booleanValueLabel(boolValue),
                tone: boolValue ? .positive : .critical
            )
        } else {
            Text(summaryText)
                .font(.headline)
        }
    }

    private var summaryText: String {
        guard let value = card.value else {
            return strings.text(.none)
        }
        if let string = value.stringValue {
            return strings.summaryValueLabel(key: card.key, value: string)
        }
        return value.displayText
    }
}
