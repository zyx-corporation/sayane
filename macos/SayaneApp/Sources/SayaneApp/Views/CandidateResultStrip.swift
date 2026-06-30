import SwiftUI

struct CandidateResultStrip: View {
    let strings: AppStrings
    let record: AppModel.CandidateActionRecord

    var body: some View {
        GroupBox(strings.text(.candidateResult)) {
            HStack(alignment: .top, spacing: 10) {
                StatusBadge(text: record.title, tone: record.tone)
                Text(record.message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                Text(strings.text(.resultForCurrentCandidate))
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}
