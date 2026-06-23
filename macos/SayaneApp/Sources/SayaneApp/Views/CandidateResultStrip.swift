import SwiftUI

struct CandidateResultStrip: View {
    let strings: AppStrings
    let record: AppModel.CandidateActionRecord

    var body: some View {
        GroupBox(strings.text(.candidateResult)) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    StatusBadge(text: record.title, tone: record.tone)
                    Spacer()
                    Text(strings.text(.resultForCurrentCandidate))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Text(record.message)
                    .font(.subheadline)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}
