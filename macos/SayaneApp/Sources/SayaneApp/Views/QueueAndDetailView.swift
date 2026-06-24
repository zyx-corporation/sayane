import SwiftUI

struct QueueAndDetailView: View {
    @ObservedObject var model: AppModel
    private struct ReviewActionItem: Identifiable {
        let id: String
        let title: String
        let enabled: Bool
        let shortcut: KeyboardShortcut
        let action: () -> Void
    }

    private struct ActionReadinessItem: Identifiable {
        let id: String
        let label: String
        let enabled: Bool
    }

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
                        HStack { Text(model.strings.residentValueLabel(section.section)); Spacer(); Text(String(section.count)) }
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
                        Text(item.displaySummary ?? item.section.map(model.strings.residentValueLabel) ?? item.status.map(model.strings.statusValueLabel) ?? model.strings.text(.none))
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        HStack(spacing: 10) {
                            if let status = item.status {
                                Label(model.strings.statusValueLabel(status), systemImage: "circle.fill")
                                    .labelStyle(.titleAndIcon)
                            }
                            if let section = item.section {
                                Text(model.strings.residentValueLabel(section))
                            }
                        }
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        HStack(spacing: 10) {
                            if let proposalSection = item.proposalSection {
                                Text("\(model.strings.fieldLabel("proposal_section")): \(model.strings.residentValueLabel(proposalSection))")
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
                            Text(model.strings.residentValueLabel(section)).tag(section)
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
                            return "\(model.strings.residentValueLabel(section)) (\(count))"
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
                detailCopyActions
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

    private var detailCopyActions: some View {
        HStack(spacing: 8) {
            Button(model.strings.text(.copyDetail)) {
                model.copySelectedCandidateDetail()
            }
            .disabled(model.detailState == nil)

            Button(model.strings.text(.copyDiff)) {
                model.copySelectedCandidateDiff()
            }
            .disabled(model.diffState == nil)

            Button(model.strings.text(.copyLineage)) {
                model.copySelectedCandidateLineage()
            }
            .disabled(model.lineageState == nil)

            Spacer()
        }
    }

    private var reviewCommandDeck: some View {
        GroupBox(model.strings.text(.commandDeck)) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.actionReadiness))
                    .font(.headline)
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(actionReadinessItems) { item in
                            StatusBadge(text: item.label, tone: item.enabled ? .positive : .neutral)
                        }
                    }
                }
                Divider()
                Text(model.strings.text(.queueActions))
                    .font(.headline)
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                    ForEach(reviewActionItems) { item in
                        Button(item.title) { item.action() }
                            .keyboardShortcut(item.shortcut)
                            .disabled(!item.enabled)
                    }
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
                DetailLabelValueRow(
                    label: model.strings.fieldLabel("status"),
                    value: summary.status.map(model.strings.statusValueLabel) ?? model.strings.text(.none)
                )
                DetailLabelValueRow(
                    label: model.strings.fieldLabel("section"),
                    value: summary.section.map(model.strings.residentValueLabel) ?? model.strings.text(.none)
                )
                DetailLabelValueRow(
                    label: model.strings.fieldLabel("operation"),
                    value: summary.operation.map(model.strings.residentValueLabel) ?? model.strings.text(.none)
                )
                DetailLabelValueRow(
                    label: model.strings.fieldLabel("rde"),
                    value: summary.rdeClass.map(model.strings.residentValueLabel) ?? model.strings.text(.none)
                )
                if let sourceType = summary.sourceType {
                    DetailLabelValueRow(
                        label: model.strings.fieldLabel("source_type"),
                        value: model.strings.residentValueLabel(sourceType)
                    )
                }
                if let evaluationLevel = summary.evaluationLevel {
                    DetailLabelValueRow(
                        label: model.strings.text(.evaluateLevel),
                        value: model.strings.evaluationLevelLabel(evaluationLevel)
                    )
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
            values.append("\(model.strings.fieldLabel("section")): \(model.strings.residentValueLabel(selectedSectionFilter))")
        }
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        if !query.isEmpty {
            values.append("\"\(query)\"")
        }
        return values
    }

    private var actionReadinessItems: [ActionReadinessItem] {
        let actions = model.detailState?.allowedActions
        return [
            ActionReadinessItem(id: "evaluate", label: "\(model.strings.text(.evaluate)) · \(stateLabel(actions?.evaluate ?? false))", enabled: actions?.evaluate ?? false),
            ActionReadinessItem(id: "approve", label: "\(model.strings.text(.approve)) · \(stateLabel(actions?.approve ?? false))", enabled: actions?.approve ?? false),
            ActionReadinessItem(id: "reject", label: "\(model.strings.text(.reject)) · \(stateLabel(actions?.reject ?? false))", enabled: actions?.reject ?? false),
            ActionReadinessItem(id: "revise", label: "\(model.strings.text(.revise)) · \(stateLabel(actions?.revise ?? false))", enabled: actions?.revise ?? false),
        ]
    }

    private var reviewActionItems: [ReviewActionItem] {
        let actions = model.detailState?.allowedActions
        return [
            ReviewActionItem(
                id: "evaluate",
                title: model.strings.text(.evaluate),
                enabled: actions?.evaluate ?? false,
                shortcut: KeyboardShortcut("e", modifiers: [.command]),
                action: { model.showingEvaluateSheet = true }
            ),
            ReviewActionItem(
                id: "approve",
                title: model.strings.text(.approve),
                enabled: actions?.approve ?? false,
                shortcut: KeyboardShortcut(.return, modifiers: [.command]),
                action: { Task { await model.approveSelected() } }
            ),
            ReviewActionItem(
                id: "reject",
                title: model.strings.text(.reject),
                enabled: actions?.reject ?? false,
                shortcut: KeyboardShortcut(.delete, modifiers: [.command]),
                action: { model.showingRejectSheet = true }
            ),
            ReviewActionItem(
                id: "revise",
                title: model.strings.text(.revise),
                enabled: actions?.revise ?? false,
                shortcut: KeyboardShortcut("m", modifiers: [.command]),
                action: { model.showingReviseSheet = true }
            ),
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
            item.displaySummary ?? item.section.map(model.strings.residentValueLabel) ?? item.status.map(model.strings.statusValueLabel) ?? model.strings.text(.none),
            item.status.map(model.strings.statusValueLabel),
            item.section.map(model.strings.residentValueLabel),
            item.proposalSection.map { "\(model.strings.fieldLabel("proposal_section")): \(model.strings.residentValueLabel($0))" },
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
                if let section = diff.section { Text("\(strings.fieldLabel("section")): \(strings.residentValueLabel(section))") }
                if let recommendedSection = diff.recommendedSection {
                    HStack {
                        Text("\(strings.fieldLabel("recommended_section")):")
                        StatusBadge(text: strings.residentValueLabel(recommendedSection), tone: .caution)
                    }
                }
                if let reviewSurface = diff.reviewSurface {
                    Text("\(strings.fieldLabel("review_surface")): \(strings.residentValueLabel(reviewSurface))")
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
                            Text(localizedLineageSummary(for: entry)).bold()
                            if let event = entry.details["event"] {
                                HStack {
                                    Text("\(strings.text(.timelineEvent)):")
                                    StatusBadge(text: localizedLineageValue(for: "event", value: event), tone: primaryLineageTone(for: entry))
                                }
                            }
                            ForEach(orderedLineageDetailKeys(entry.details.keys), id: \.self) { key in
                                if key != "event" {
                                    DetailLabelValueRow(
                                        label: strings.lineageDetailLabel(key),
                                        value: localizedLineageValue(for: key, value: entry.details[key] ?? "")
                                    )
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
        if key.hasSuffix("_at") {
            return formattedLineageTimestamp(value)
        }
        if key == "status" || key == "decision" || key == "event" || key == "from_status" || key == "to_status" {
            return strings.statusValueLabel(value)
        }
        if key == "operation" || key == "section" || key == "proposal_section" || key == "recommended_section" || key == "review_surface" || key == "source_type" || key == "rde" || key.hasSuffix("_section") {
            return strings.residentValueLabel(value)
        }
        return value
    }

    private func formattedLineageTimestamp(_ rawValue: String) -> String {
        guard let date = ISO8601DateFormatter().date(from: rawValue) else { return rawValue }
        let relativeFormatter = RelativeDateTimeFormatter()
        relativeFormatter.unitsStyle = .short
        let relative = relativeFormatter.localizedString(for: date, relativeTo: Date())
        let absolute = date.formatted(date: .abbreviated, time: .shortened)
        return "\(relative) (\(absolute))"
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

    private func localizedLineageSummary(for entry: LineageEntry) -> String {
        if let event = entry.details["event"] {
            var components = [localizedLineageValue(for: "event", value: event)]
            if let section = entry.details["proposal_section"] ?? entry.details["section"] {
                components.append(localizedLineageValue(for: "section", value: section))
            } else if let status = entry.details["status"] {
                components.append(localizedLineageValue(for: "status", value: status))
            }
            return components.joined(separator: " · ")
        }
        if let decision = entry.details["decision"] {
            var components = [localizedLineageValue(for: "decision", value: decision)]
            if let status = entry.details["to_status"] ?? entry.details["status"] {
                components.append(localizedLineageValue(for: "status", value: status))
            }
            return components.joined(separator: " · ")
        }
        if let operation = entry.details["operation"] {
            var components = [localizedLineageValue(for: "operation", value: operation)]
            if let status = entry.details["status"] {
                components.append(localizedLineageValue(for: "status", value: status))
            }
            return components.joined(separator: " · ")
        }
        if let status = entry.details["status"] {
            return localizedLineageValue(for: "status", value: status)
        }
        return entry.summary
    }

    private func primaryLineageTone(for entry: LineageEntry) -> StatusTone {
        if let event = entry.details["event"] {
            return toneForLineageToken(event)
        }
        if let decision = entry.details["decision"] {
            return toneForLineageToken(decision)
        }
        if let status = entry.details["to_status"] ?? entry.details["status"] {
            return toneForLineageToken(status)
        }
        return .neutral
    }

    private func toneForLineageToken(_ token: String) -> StatusTone {
        switch token {
        case "approved", "candidate_approved", "captured":
            return .positive
        case "rejected", "candidate_rejected", "reject":
            return .critical
        case "evaluated", "candidate_evaluated", "candidate_revised", "revised", "pending":
            return .caution
        default:
            return strings.tone(forToken: token)
        }
    }

    private func orderedLineageDetailKeys<S: Sequence>(_ keys: S) -> [String] where S.Element == String {
        keys.sorted { lhs, rhs in
            let lhsPriority = lineageDetailPriority(lhs)
            let rhsPriority = lineageDetailPriority(rhs)
            if lhsPriority != rhsPriority {
                return lhsPriority < rhsPriority
            }
            return lhs < rhs
        }
    }

    private func lineageDetailPriority(_ key: String) -> Int {
        switch key {
        case "event":
            return 0
        case "decision", "status", "from_status", "to_status", "operation":
            return 1
        case "section", "proposal_section", "recommended_section", "review_surface", "source_type", "rde":
            return 2
        case "created_at", "captured_at", "evaluated_at", "approved_at", "rejected_at":
            return 3
        case "candidate_id", "source_candidate_id", "revised_candidate_id":
            return 4
        default:
            return 5
        }
    }
}
