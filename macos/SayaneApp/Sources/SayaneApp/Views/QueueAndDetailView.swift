import SwiftUI

struct QueueAndDetailView: View {
    @ObservedObject var model: AppModel
    private enum SortMode: String, CaseIterable {
        case newest
        case status
        case section
    }

    @State private var searchText = ""
    @State private var selectedStatusFilter = ""
    @State private var selectedSectionFilter = ""
    @State private var sortMode: SortMode = .newest

    var body: some View {
        HSplitView {
            queuePane
                .frame(minWidth: 320)
            detailPane
                .frame(minWidth: 520)
        }
        .navigationTitle(model.strings.text(.queue))
        .toolbar {
            ToolbarItemGroup {
                Button(model.strings.text(.previousCandidate)) {
                    model.selectPreviousCandidate()
                }
                .disabled(!model.hasPreviousCandidate)
                .keyboardShortcut(.leftArrow, modifiers: [.command])

                Button(model.strings.text(.nextCandidate)) {
                    model.selectNextCandidate()
                }
                .disabled(!model.hasNextCandidate)
                .keyboardShortcut(.rightArrow, modifiers: [.command])
            }
        }
        .sheet(isPresented: $model.showingEvaluateSheet) {
            EvaluateSheet(model: model)
        }
        .sheet(isPresented: $model.showingRejectSheet) {
            RejectSheet(model: model)
        }
        .sheet(isPresented: $model.showingReviseSheet) {
            ReviseSheet(model: model)
        }
    }

    private var queuePane: some View {
        VStack(alignment: .leading, spacing: 12) {
            BridgeStatusPanel(model: model, compact: true)
            Text("\(model.strings.text(.reviewableCount)): \(model.queueState?.reviewableCount ?? 0)")
                .font(.headline)
            queueStatusBar
            filterBar
            quickFilterBar
            if let statusCounts = model.queueState?.statusCounts, !statusCounts.isEmpty {
                GroupBox(model.strings.text(.statusCounts)) {
                    ForEach(statusCounts.keys.sorted(), id: \.self) { key in
                        HStack {
                            Text(model.strings.statusValueLabel(key))
                            Spacer()
                            Text(String(statusCounts[key] ?? 0))
                        }
                    }
                }
            }
            if let topSections = model.queueState?.topSections, !topSections.isEmpty {
                GroupBox(model.strings.text(.topSections)) {
                    ForEach(topSections) { section in
                        HStack { Text(section.section); Spacer(); Text(String(section.count)) }
                    }
                }
            }
            if model.isLoading && model.queueState == nil {
                StateCardView(
                    icon: "arrow.triangle.2.circlepath",
                    title: model.strings.text(.loadingState),
                    message: model.strings.text(.loadingCandidates),
                    tone: .caution,
                    badgeText: model.strings.text(.bridgeAttention)
                )
            } else if filteredItems.isEmpty {
                StateCardView(
                    icon: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty ? "tray" : "line.3.horizontal.decrease.circle",
                    title: model.strings.text(.queue),
                    message: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty
                        ? model.strings.text(.noCandidates)
                        : model.strings.text(.noCandidatesMatchingFilters),
                    tone: .neutral,
                    badgeText: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty
                        ? nil
                        : model.strings.text(.activeFilters),
                    actionTitle: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty
                        ? model.strings.text(.refresh)
                        : model.strings.text(.clearFilters),
                    action: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty
                        ? { Task { await model.refreshCurrentScreen() } }
                        : clearFilters
                )
            } else {
                List(filteredItems, selection: Binding(
                    get: { model.selectedCandidateID },
                    set: { if let value = $0 { model.chooseCandidate(value) } }
                )) { item in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(item.id).font(.headline)
                        Text(item.displaySummary ?? item.section ?? item.status ?? model.strings.text(.none))
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        HStack(spacing: 10) {
                            if let status = item.status {
                                Label(model.strings.statusValueLabel(status), systemImage: "circle.fill")
                                    .labelStyle(.titleAndIcon)
                            }
                            if let section = item.section {
                                Text(section)
                            }
                        }
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        HStack(spacing: 10) {
                            if let proposalSection = item.proposalSection {
                                Text("\(model.strings.fieldLabel("proposal_section")): \(proposalSection)")
                            }
                            if let capturedAt = formattedCapturedAt(item.capturedAt) {
                                Text("\(model.strings.fieldLabel("captured_at")): \(capturedAt)")
                            }
                        }
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                    }
                    .padding(.vertical, 4)
                    .accessibilityLabel(candidateAccessibilityLabel(item))
                }
            }
        }
        .padding()
    }

    private var queueStatusBar: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    StatusBadge(
                        text: "\(model.strings.text(.filteredCandidates)): \(filteredItems.count)",
                        tone: filteredItems.isEmpty ? .neutral : .positive
                    )
                    StatusBadge(
                        text: "\(model.strings.text(.sortOrder)): \(sortModeLabel)",
                        tone: .neutral
                    )
                    Spacer()
                }
                HStack(alignment: .top, spacing: 8) {
                    Text("\(model.strings.text(.activeFilters)):")
                        .font(.caption.weight(.semibold))
                    if activeFilterLabels.isEmpty {
                        Text(model.strings.text(.noActiveFilters))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    } else {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 6) {
                                ForEach(activeFilterLabels, id: \.self) { label in
                                    StatusBadge(text: label, tone: .caution)
                                }
                            }
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var filterBar: some View {
        GroupBox(model.strings.text(.filters)) {
            VStack(alignment: .leading, spacing: 8) {
                TextField(model.strings.text(.searchCandidates), text: $searchText)
                    .textFieldStyle(.roundedBorder)
                HStack {
                    Picker(model.strings.text(.status), selection: $selectedStatusFilter) {
                        Text(model.strings.text(.allStatuses)).tag("")
                        ForEach(availableStatuses, id: \.self) { status in
                            Text(model.strings.statusValueLabel(status)).tag(status)
                        }
                    }
                    Picker(model.strings.fieldLabel("section"), selection: $selectedSectionFilter) {
                        Text(model.strings.text(.allSections)).tag("")
                        ForEach(availableSections, id: \.self) { section in
                            Text(section).tag(section)
                        }
                    }
                    Picker(model.strings.text(.sortOrder), selection: $sortMode) {
                        Text(model.strings.text(.sortNewest)).tag(SortMode.newest)
                        Text(model.strings.text(.sortStatus)).tag(SortMode.status)
                        Text(model.strings.text(.sortSection)).tag(SortMode.section)
                    }
                    Button(model.strings.text(.clearFilters)) {
                        searchText = ""
                        selectedStatusFilter = ""
                        selectedSectionFilter = ""
                        sortMode = .newest
                    }
                    .disabled(searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty && sortMode == .newest)
                }
            }
        }
    }

    private var quickFilterBar: some View {
        GroupBox(model.strings.text(.quickFilters)) {
            VStack(alignment: .leading, spacing: 8) {
                if let statusCounts = model.queueState?.statusCounts, !statusCounts.isEmpty {
                    quickFilterChipGroup(
                        title: model.strings.text(.statusCounts),
                        items: statusCounts.keys.sorted(),
                        selection: selectedStatusFilter,
                        label: { key in "\(model.strings.statusValueLabel(key)) (\(statusCounts[key] ?? 0))" },
                        action: { key in toggleStatusFilter(key) }
                    )
                }
                if let topSections = model.queueState?.topSections, !topSections.isEmpty {
                    quickFilterChipGroup(
                        title: model.strings.text(.topSections),
                        items: topSections.map(\.section),
                        selection: selectedSectionFilter,
                        label: { section in
                            let count = topSections.first(where: { $0.section == section })?.count ?? 0
                            return "\(section) (\(count))"
                        },
                        action: { section in toggleSectionFilter(section) }
                    )
                }
            }
        }
    }

    private var detailPane: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                if let candidateID = model.selectedCandidateID {
                    Text("\(model.strings.text(.currentCandidate)): \(candidateID)")
                        .font(.title2).bold()
                }
                if let record = model.selectedCandidateActionRecord {
                    CandidateResultStrip(strings: model.strings, record: record)
                }
                if model.isLoading && model.detailState == nil && model.selectedCandidateID != nil {
                    StateCardView(
                        icon: "arrow.triangle.2.circlepath",
                        title: model.strings.text(.loadingState),
                        message: model.strings.text(.loadingCandidates),
                        tone: .caution,
                        badgeText: model.strings.text(.bridgeAttention)
                    )
                } else if model.selectedCandidateID == nil {
                    StateCardView(
                        icon: "rectangle.and.text.magnifyingglass",
                        title: model.strings.text(.detail),
                        message: model.strings.text(.selectCandidatePrompt),
                        tone: .neutral,
                        badgeText: model.strings.text(.queue),
                        actionTitle: model.strings.text(.refresh),
                        action: { Task { await model.refreshCurrentScreen() } }
                    )
                } else if model.detailState == nil {
                    StateCardView(
                        icon: "exclamationmark.bubble",
                        title: model.strings.text(.detail),
                        message: model.strings.text(.detailUnavailable),
                        tone: .caution,
                        badgeText: model.strings.text(.needsAttention),
                        actionTitle: model.strings.text(.retry),
                        action: {
                            guard let candidateID = model.selectedCandidateID else { return }
                            Task {
                                do {
                                    try await model.loadCandidate(candidateID: candidateID)
                                } catch {
                                    model.errorMessage = error.localizedDescription
                                }
                            }
                        }
                    )
                } else {
                    if let summary = model.detailState?.uiSummary {
                        detailSummary(summary)
                    }
                    reviewCommandDeck
                    if let content = model.detailState?.content {
                        GroupBox(model.strings.text(.detail)) {
                            Text(content)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    if let diff = model.diffState {
                        DiffSection(strings: model.strings, diff: diff)
                    }
                    if let lineage = model.lineageState {
                        LineageSection(strings: model.strings, lineage: lineage)
                    }
                }
            }
            .padding(24)
        }
    }

    private var reviewCommandDeck: some View {
        GroupBox(model.strings.text(.commandDeck)) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.actionReadiness))
                    .font(.headline)
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(actionReadinessItems, id: \.label) { item in
                            StatusBadge(text: item.label, tone: item.enabled ? .positive : .neutral)
                        }
                    }
                }
                Divider()
                Text(model.strings.text(.queueActions))
                    .font(.headline)
                HStack {
                    Button(model.strings.text(.evaluate)) { model.showingEvaluateSheet = true }
                        .keyboardShortcut("e", modifiers: [.command])
                        .disabled(!(model.detailState?.allowedActions.evaluate ?? false))
                    Button(model.strings.text(.approve)) {
                        Task { await model.approveSelected() }
                    }
                    .keyboardShortcut(.return, modifiers: [.command])
                    .disabled(!(model.detailState?.allowedActions.approve ?? false))
                    Button(model.strings.text(.reject)) { model.showingRejectSheet = true }
                        .keyboardShortcut(.delete, modifiers: [.command])
                        .disabled(!(model.detailState?.allowedActions.reject ?? false))
                    Button(model.strings.text(.revise)) { model.showingReviseSheet = true }
                        .keyboardShortcut("m", modifiers: [.command])
                        .disabled(!(model.detailState?.allowedActions.revise ?? false))
                }
                Divider()
                Text(model.strings.text(.shortcutGuide))
                    .font(.headline)
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(actionShortcutHints, id: \.self) { hint in
                        Text(hint)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func detailSummary(_ summary: CandidateUISummary) -> some View {
        GroupBox(model.strings.text(.summaryCards)) {
            VStack(alignment: .leading, spacing: 8) {
                Text("\(model.strings.fieldLabel("status")): \(summary.status.map(model.strings.statusValueLabel) ?? model.strings.text(.none))")
                Text("\(model.strings.fieldLabel("section")): \(summary.section ?? model.strings.text(.none))")
                Text("\(model.strings.fieldLabel("operation")): \(summary.operation ?? model.strings.text(.none))")
                Text("\(model.strings.fieldLabel("rde")): \(summary.rdeClass ?? model.strings.text(.none))")
                if let sourceType = summary.sourceType {
                    Text("\(model.strings.fieldLabel("source_type")): \(sourceType)")
                }
                if let evaluationLevel = summary.evaluationLevel {
                    Text("\(model.strings.text(.evaluateLevel)): \(evaluationLevel)")
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var filteredItems: [CandidateItem] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let filtered = (model.queueState?.items ?? []).filter { item in
            let matchesStatus = selectedStatusFilter.isEmpty || item.status == selectedStatusFilter
            let matchesSection = selectedSectionFilter.isEmpty || item.section == selectedSectionFilter
            let haystack = [
                item.id,
                item.status,
                item.section,
                item.displaySummary,
                item.proposalSection,
                item.content,
            ]
            .compactMap { $0?.lowercased() }
            .joined(separator: "\n")
            let matchesQuery = query.isEmpty || haystack.contains(query)
            return matchesStatus && matchesSection && matchesQuery
        }
        switch sortMode {
        case .newest:
            return filtered.sorted {
                ($0.capturedAt ?? "") > ($1.capturedAt ?? "")
            }
        case .status:
            return filtered.sorted {
                let lhs = ($0.status ?? "") + "::" + ($0.capturedAt ?? "")
                let rhs = ($1.status ?? "") + "::" + ($1.capturedAt ?? "")
                return lhs > rhs
            }
        case .section:
            return filtered.sorted {
                let lhs = ($0.section ?? "") + "::" + ($0.capturedAt ?? "")
                let rhs = ($1.section ?? "") + "::" + ($1.capturedAt ?? "")
                return lhs > rhs
            }
        }
    }

    private func clearFilters() {
        searchText = ""
        selectedStatusFilter = ""
        selectedSectionFilter = ""
        sortMode = .newest
    }

    private var availableStatuses: [String] {
        Array(Set((model.queueState?.items ?? []).compactMap(\.status))).sorted()
    }

    private var availableSections: [String] {
        Array(Set((model.queueState?.items ?? []).compactMap(\.section))).sorted()
    }

    private func formattedCapturedAt(_ rawValue: String?) -> String? {
        guard let rawValue, !rawValue.isEmpty else { return nil }
        guard let date = ISO8601DateFormatter().date(from: rawValue) else { return rawValue }
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .short
        let relative = formatter.localizedString(for: date, relativeTo: Date())
        let fallback = date.formatted(date: .abbreviated, time: .shortened)
        return "\(relative) (\(fallback))"
    }

    private func toggleStatusFilter(_ status: String) {
        selectedStatusFilter = selectedStatusFilter == status ? "" : status
    }

    private func toggleSectionFilter(_ section: String) {
        selectedSectionFilter = selectedSectionFilter == section ? "" : section
    }

    private var sortModeLabel: String {
        switch sortMode {
        case .newest:
            return model.strings.text(.sortNewest)
        case .status:
            return model.strings.text(.sortStatus)
        case .section:
            return model.strings.text(.sortSection)
        }
    }

    private var activeFilterLabels: [String] {
        var values: [String] = []
        if !selectedStatusFilter.isEmpty {
            values.append("\(model.strings.text(.status)): \(model.strings.statusValueLabel(selectedStatusFilter))")
        }
        if !selectedSectionFilter.isEmpty {
            values.append("\(model.strings.fieldLabel("section")): \(selectedSectionFilter)")
        }
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        if !query.isEmpty {
            values.append("\"\(query)\"")
        }
        return values
    }

    private var actionReadinessItems: [(label: String, enabled: Bool)] {
        let actions = model.detailState?.allowedActions
        return [
            (label: "\(model.strings.text(.evaluate)) · \(stateLabel(actions?.evaluate ?? false))", enabled: actions?.evaluate ?? false),
            (label: "\(model.strings.text(.approve)) · \(stateLabel(actions?.approve ?? false))", enabled: actions?.approve ?? false),
            (label: "\(model.strings.text(.reject)) · \(stateLabel(actions?.reject ?? false))", enabled: actions?.reject ?? false),
            (label: "\(model.strings.text(.revise)) · \(stateLabel(actions?.revise ?? false))", enabled: actions?.revise ?? false),
        ]
    }

    private var actionShortcutHints: [String] {
        [
            "\(model.strings.text(.shortcutLabel)): ⌘E \(model.strings.text(.evaluate))",
            "\(model.strings.text(.shortcutLabel)): ⌘↩ \(model.strings.text(.approve))",
            "\(model.strings.text(.shortcutLabel)): ⌘⌫ \(model.strings.text(.reject))",
            "\(model.strings.text(.shortcutLabel)): ⌘M \(model.strings.text(.revise))",
        ]
    }

    private func stateLabel(_ enabled: Bool) -> String {
        enabled ? model.strings.text(.enabled) : model.strings.text(.disabled)
    }

    private func candidateAccessibilityLabel(_ item: CandidateItem) -> String {
        [
            item.id,
            item.displaySummary ?? item.section ?? item.status ?? model.strings.text(.none),
            item.status.map(model.strings.statusValueLabel),
            item.section,
            item.proposalSection.map { "\(model.strings.fieldLabel("proposal_section")): \($0)" },
        ]
        .compactMap { $0 }
        .joined(separator: " ")
    }

    @ViewBuilder
    private func quickFilterChipGroup(
        title: String,
        items: [String],
        selection: String,
        label: @escaping (String) -> String,
        action: @escaping (String) -> Void
    ) -> some View {
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                Text(title).bold()
                HStack(spacing: 6) {
                    ForEach(items, id: \.self) { item in
                        Button {
                            action(item)
                        } label: {
                            StatusBadge(
                                text: label(item),
                                tone: selection == item ? .caution : .neutral
                            )
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
}

private struct DiffSection: View {
    let strings: AppStrings
    let diff: CandidateDiffPayload

    var body: some View {
        GroupBox(strings.text(.diff)) {
            VStack(alignment: .leading, spacing: 8) {
                diffSummary
                if let note = diff.note { Text(note) }
                if let add = diff.add, !add.isEmpty {
                    diffListBlock(title: strings.text(.addedItems), tone: .positive, prefix: "+", items: add)
                }
                if let remove = diff.remove, !remove.isEmpty {
                    diffListBlock(title: strings.text(.removedItems), tone: .critical, prefix: "-", items: remove)
                }
                if let alreadyPresent = diff.alreadyPresent, !alreadyPresent.isEmpty {
                    diffListBlock(title: strings.text(.existingItems), tone: .neutral, prefix: "•", items: alreadyPresent)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private var diffSummary: some View {
        GroupBox(strings.text(.diffSummary)) {
            VStack(alignment: .leading, spacing: 8) {
                if let section = diff.section { Text("\(strings.fieldLabel("section")): \(section)") }
                if let recommendedSection = diff.recommendedSection {
                    HStack {
                        Text("\(strings.fieldLabel("recommended_section")):")
                        StatusBadge(text: recommendedSection, tone: .caution)
                    }
                }
                if let reviewSurface = diff.reviewSurface {
                    Text("\(strings.fieldLabel("review_surface")): \(reviewSurface)")
                }
                HStack(spacing: 8) {
                    if let profileUpdateRecommended = diff.profileUpdateRecommended {
                        StatusBadge(
                            text: "\(strings.fieldLabel("profile_update_recommended")): \(strings.booleanValueLabel(profileUpdateRecommended))",
                            tone: profileUpdateRecommended ? .caution : .neutral
                        )
                    }
                    if let hasDuplicates = diff.hasDuplicates {
                        StatusBadge(
                            text: "\(strings.fieldLabel("has_duplicates")): \(strings.booleanValueLabel(hasDuplicates))",
                            tone: hasDuplicates ? .critical : .positive
                        )
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func diffListBlock(title: String, tone: StatusTone, prefix: String, items: [String]) -> some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    StatusBadge(text: title, tone: tone)
                    Spacer()
                }
                ForEach(items, id: \.self) { item in
                    Text("\(prefix) \(item)")
                        .font(.system(.body, design: .monospaced))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(tone.backgroundStyle, in: RoundedRectangle(cornerRadius: 8))
                }
            }
        }
    }
}

private struct LineageSection: View {
    let strings: AppStrings
    let lineage: CandidateLineagePayload

    var body: some View {
        GroupBox(strings.text(.lineage)) {
            VStack(alignment: .leading, spacing: 8) {
                Text(lineage.candidateId).font(.headline)
                ForEach(lineage.lineageEntries ?? []) { entry in
                    SurfaceCard(emphasis: 0) {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                StatusBadge(
                                    text: primaryLineageLabel(for: entry),
                                    tone: primaryLineageTone(for: entry)
                                )
                                Spacer()
                            }
                            Text(entry.summary).bold()
                            if let event = entry.details["event"] {
                                HStack {
                                    Text("\(strings.text(.timelineEvent)):")
                                    StatusBadge(text: localizedLineageValue(for: "event", value: event), tone: primaryLineageTone(for: entry))
                                }
                            }
                            ForEach(entry.details.keys.sorted(), id: \.self) { key in
                                if key != "event" {
                                    Text("\(strings.lineageDetailLabel(key)): \(localizedLineageValue(for: key, value: entry.details[key] ?? ""))")
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                    .background(primaryLineageTone(for: entry).backgroundStyle, in: RoundedRectangle(cornerRadius: 12))
                    .padding(.vertical, 4)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func localizedLineageValue(for key: String, value: String) -> String {
        if key == "status" || key == "decision" || key == "event" || key == "operation" {
            return strings.statusValueLabel(value)
        }
        return value
    }

    private func primaryLineageLabel(for entry: LineageEntry) -> String {
        if let event = entry.details["event"] {
            return localizedLineageValue(for: "event", value: event)
        }
        if let decision = entry.details["decision"] {
            return localizedLineageValue(for: "decision", value: decision)
        }
        if let status = entry.details["status"] {
            return localizedLineageValue(for: "status", value: status)
        }
        return entry.summary
    }

    private func primaryLineageTone(for entry: LineageEntry) -> StatusTone {
        let source = entry.details["event"] ?? entry.details["decision"] ?? entry.details["status"] ?? ""
        if source.contains("approved") {
            return .positive
        }
        if source.contains("rejected") || source.contains("reject") {
            return .critical
        }
        if source.contains("revised") || source.contains("pending") || source.contains("evaluated") {
            return .caution
        }
        return .neutral
    }
}
