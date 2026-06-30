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
    @State private var showsLowerPanel = false
    @State private var selectedLowerPanel: LowerPanelTab = .diff

    private enum LowerPanelTab: String {
        case diff
        case lineage
    }

    var body: some View {
        HSplitView {
            queuePane
                .frame(minWidth: 320, idealWidth: 320, maxWidth: 320)
            detailPane
                .frame(minWidth: 520, idealWidth: 640)
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
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
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                StatusBadge(
                    text: "\(model.queueState?.reviewableCount ?? 0) \(model.strings.text(.reviewableCount))",
                    tone: (model.queueState?.reviewableCount ?? 0) > 0 ? .positive : .neutral
                )
                if !activeFilterLabels.isEmpty {
                    StatusBadge(
                        text: "\(activeFilterLabels.count) \(model.strings.text(.activeFilters))",
                        tone: .caution
                    )
                }
                Spacer()
                Button(model.toolbarRefreshText) {
                    Task { await model.refreshCurrentScreen() }
                }
                .buttonStyle(.plain)
                .font(.caption.weight(.semibold))
            }
            filterBar
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
                        ? model.queueEmptyMessage
                        : model.strings.text(.noCandidatesMatchingFilters),
                    tone: .neutral,
                    badgeText: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty
                        ? model.queueEmptyBadgeText
                        : model.strings.text(.activeFilters),
                    actionTitle: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty
                        ? model.toolbarRefreshText
                        : model.strings.text(.clearFilters),
                    actionEnabled: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty
                        ? !model.bridgeRecoveryActionDisabled
                        : true,
                    action: searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty
                        ? { Task { await model.refreshCurrentScreen() } }
                        : clearFilters
                )
            } else {
                List(filteredItems, selection: Binding(
                    get: { model.selectedCandidateID },
                    set: { if let value = $0 { model.chooseCandidate(value) } }
                )) { item in
                    VStack(alignment: .leading, spacing: 3) {
                        HStack(spacing: 6) {
                            if let status = item.status {
                                StatusBadge(text: model.strings.statusValueLabel(status), tone: model.strings.tone(forToken: status))
                            }
                            Text(item.id).font(.subheadline.weight(.semibold))
                            Spacer()
                        }
                        Text(item.displaySummary ?? item.section.map(model.strings.residentValueLabel) ?? item.status.map(model.strings.statusValueLabel) ?? model.strings.text(.none))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                        HStack(spacing: 8) {
                            if let section = item.section {
                                Text(model.strings.residentValueLabel(section))
                            }
                            if let proposalSection = item.proposalSection {
                                Text(model.strings.residentValueLabel(proposalSection))
                            }
                            if let capturedAt = formattedCapturedAt(item.capturedAt) {
                                Text(capturedAt)
                            }
                        }
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                    }
                    .padding(.vertical, 3)
                    .accessibilityLabel(candidateAccessibilityLabel(item))
                }
                .frame(maxWidth: .infinity, alignment: .topLeading)
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .background(Color(NSColor.controlBackgroundColor).opacity(0.32))
    }

    private var filterBar: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 8) {
                TextField(model.strings.text(.searchCandidates), text: $searchText)
                    .textFieldStyle(.roundedBorder)
                HStack(spacing: 8) {
                    Picker(model.strings.text(.sortOrder), selection: $sortMode) {
                        Text(model.strings.text(.sortNewest)).tag(SortMode.newest)
                        Text(model.strings.text(.sortStatus)).tag(SortMode.status)
                        Text(model.strings.text(.sortSection)).tag(SortMode.section)
                    }
                    .labelsHidden()
                    .frame(maxWidth: 180)
                    if !activeFilterLabels.isEmpty {
                        StatusBadge(text: "\(activeFilterLabels.count) \(model.strings.text(.activeFilters))", tone: .caution)
                    }
                    Spacer()
                    Button(model.strings.text(.clearFilters)) {
                        searchText = ""
                        selectedStatusFilter = ""
                        selectedSectionFilter = ""
                        sortMode = .newest
                    }
                    .disabled(searchText.isEmpty && selectedStatusFilter.isEmpty && selectedSectionFilter.isEmpty && sortMode == .newest)
                }
                if !quickFilterItems.isEmpty {
                    FlowLayout(quickFilterItems, id: \.id, spacing: 6) { item in
                        Button {
                            item.action()
                        } label: {
                            StatusBadge(text: item.label, tone: item.selected ? .caution : .neutral)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }

    private var detailPane: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
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
                        message: model.detailEmptyMessage,
                        tone: .neutral,
                        badgeText: model.detailEmptyBadgeText,
                        actionTitle: model.toolbarRefreshText,
                        actionEnabled: !model.bridgeRecoveryActionDisabled,
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
                    detailHeader
                    reviewCommandDeck
                    if let content = model.detailState?.content {
                        bodySection(title: model.strings.text(.detail)) {
                            Text(content)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    lowerPanelSection
                    evidenceDrilldownSection
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .background(Color(NSColor.controlBackgroundColor).opacity(0.22))
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

    @ViewBuilder
    private var detailHeader: some View {
        if let summary = model.detailState?.uiSummary {
            SurfaceCard(emphasis: 0.22) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(alignment: .top, spacing: 10) {
                        VStack(alignment: .leading, spacing: 6) {
                            if let candidateID = model.selectedCandidateID {
                                Text(candidateID)
                                    .font(.headline).bold()
                            }
                            Text(detailHeaderSummaryText(summary))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 6) {
                            if let status = summary.status {
                                StatusBadge(text: model.strings.statusValueLabel(status), tone: model.strings.tone(forToken: status))
                            }
                            HStack(spacing: 6) {
                                if let section = summary.section {
                                    StatusBadge(text: model.strings.residentValueLabel(section), tone: .neutral)
                                }
                                if let evaluationLevel = summary.evaluationLevel {
                                    StatusBadge(text: model.strings.evaluationLevelLabel(evaluationLevel), tone: .caution)
                                }
                            }
                        }
                    }
                    detailSummary(summary)
                }
            }
        }
    }

    private func compactDisclosureSection<Content: View>(
        title: String,
        isExpanded: Binding<Bool>,
        @ViewBuilder content: @escaping () -> Content
    ) -> some View {
        GroupBox {
            DisclosureGroup(isExpanded: isExpanded) {
                VStack(alignment: .leading, spacing: 8) {
                    content()
                }
                .padding(.top, 8)
            } label: {
                Text(title)
                    .font(.headline)
            }
        }
    }

    private func bodySection<Content: View>(
        title: String,
        @ViewBuilder content: @escaping () -> Content
    ) -> some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(.headline)
                content()
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var evidenceDrilldownSection: some View {
        GroupBox(model.strings.text(.evidenceDrilldown)) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.evidenceDrilldownSummary))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack(spacing: 8) {
                    if model.detailState != nil {
                        StatusBadge(text: model.strings.text(.detail), tone: .positive)
                    }
                    if model.diffState != nil {
                        StatusBadge(text: model.strings.text(.diff), tone: .caution)
                    }
                    if model.lineageState != nil {
                        StatusBadge(text: model.strings.text(.lineage), tone: .neutral)
                    }
                    Spacer()
                }
                detailCopyActions
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var reviewCommandDeck: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 10) {
                HStack(spacing: 8) {
                    ForEach(reviewActionItems) { item in
                        reviewActionButton(item)
                    }
                    Spacer()
                    if let firstDisabled = actionReadinessItems.first(where: { !$0.enabled }) {
                        StatusBadge(text: firstDisabled.label, tone: .neutral)
                    }
                }
                Text(actionShortcutHints.joined(separator: " · "))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func detailSummary(_ summary: CandidateUISummary) -> some View {
        GroupBox {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 150), spacing: 8)], spacing: 8) {
                summaryChip(label: model.strings.fieldLabel("operation"), value: summary.operation.map(model.strings.residentValueLabel) ?? model.strings.text(.none))
                summaryChip(label: model.strings.fieldLabel("rde"), value: summary.rdeClass.map(model.strings.residentValueLabel) ?? model.strings.text(.none))
                if let sourceType = summary.sourceType {
                    summaryChip(label: model.strings.fieldLabel("source_type"), value: model.strings.residentValueLabel(sourceType))
                }
                if let evaluationLevel = summary.evaluationLevel {
                    summaryChip(label: model.strings.text(.evaluateLevel), value: model.strings.evaluationLevelLabel(evaluationLevel))
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private var lowerPanelSection: some View {
        if model.diffState != nil || model.lineageState != nil {
            GroupBox {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 10) {
                        Button {
                            selectedLowerPanel = .diff
                            withAnimation(.easeInOut(duration: 0.16)) { showsLowerPanel = true }
                        } label: {
                            lowerPanelTabLabel(model.strings.text(.diff), selected: selectedLowerPanel == .diff && showsLowerPanel)
                        }
                        .buttonStyle(.plain)
                        .disabled(model.diffState == nil)

                        Button {
                            selectedLowerPanel = .lineage
                            withAnimation(.easeInOut(duration: 0.16)) { showsLowerPanel = true }
                        } label: {
                            lowerPanelTabLabel(model.strings.text(.lineage), selected: selectedLowerPanel == .lineage && showsLowerPanel)
                        }
                        .buttonStyle(.plain)
                        .disabled(model.lineageState == nil)

                        Spacer()

                        Button(showsLowerPanel ? "▾ 閉じる" : "▸ タップで展開") {
                            withAnimation(.easeInOut(duration: 0.16)) {
                                showsLowerPanel.toggle()
                            }
                        }
                        .buttonStyle(.plain)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    }

                    if showsLowerPanel {
                        if selectedLowerPanel == .diff, let diff = model.diffState {
                            DiffSection(strings: model.strings, diff: diff)
                        } else if selectedLowerPanel == .lineage, let lineage = model.lineageState {
                            LineageSection(strings: model.strings, lineage: lineage)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    private func lowerPanelTabLabel(_ title: String, selected: Bool) -> some View {
        Text(title)
            .font(.subheadline.weight(selected ? .bold : .semibold))
            .foregroundStyle(selected ? .primary : .secondary)
            .padding(.vertical, 4)
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(selected ? Color.primary : Color.clear)
                    .frame(height: 2)
            }
    }

    private func detailHeaderSummaryText(_ summary: CandidateUISummary) -> String {
        [
            summary.status.map(model.strings.statusValueLabel),
            summary.section.map(model.strings.residentValueLabel),
            summary.sourceType.map(model.strings.residentValueLabel),
        ]
        .compactMap { $0 }
        .joined(separator: " · ")
    }

    private func summaryChip(label: String, value: String) -> some View {
        SurfaceCard(emphasis: 0.18) {
            VStack(alignment: .leading, spacing: 3) {
                Text(label)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(value)
                    .font(.caption)
            }
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

    private var statusCountBadges: [String] {
        guard let statusCounts = model.queueState?.statusCounts else { return [] }
        let sorted = statusCounts.keys.sorted {
            let lhs = statusCounts[$0] ?? 0
            let rhs = statusCounts[$1] ?? 0
            if lhs != rhs { return lhs > rhs }
            return $0 < $1
        }
        return Array(sorted.prefix(3)).map { key in
            "\(model.strings.statusValueLabel(key)) (\(statusCounts[key] ?? 0))"
        }
    }

    private var topSectionBadges: [String] {
        guard let topSections = model.queueState?.topSections else { return [] }
        return Array(topSections.prefix(3)).map { section in
            "\(model.strings.residentValueLabel(section.section)) (\(section.count))"
        }
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

    private func reviewActionButton(_ item: ReviewActionItem) -> some View {
        let button = Button(item.title) { item.action() }
            .keyboardShortcut(item.shortcut)
            .controlSize(.small)
            .disabled(!item.enabled)

        if item.id == "approve" {
            return AnyView(button.buttonStyle(.bordered))
        }
        return AnyView(button.buttonStyle(.borderedProminent))
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

    private struct QuickFilterItem: Identifiable {
        let id: String
        let label: String
        let selected: Bool
        let action: () -> Void
    }

    private var quickFilterItems: [QuickFilterItem] {
        var items: [QuickFilterItem] = []
        if let statusCounts = model.queueState?.statusCounts {
            for key in statusCounts.keys.sorted() {
                items.append(
                    QuickFilterItem(
                        id: "status-\(key)",
                        label: "\(model.strings.statusValueLabel(key)) (\(statusCounts[key] ?? 0))",
                        selected: selectedStatusFilter == key,
                        action: { toggleStatusFilter(key) }
                    )
                )
            }
        }
        if let topSections = model.queueState?.topSections {
            for section in topSections.map(\.section) {
                let count = topSections.first(where: { $0.section == section })?.count ?? 0
                items.append(
                    QuickFilterItem(
                        id: "section-\(section)",
                        label: "\(model.strings.residentValueLabel(section)) (\(count))",
                        selected: selectedSectionFilter == section,
                        action: { toggleSectionFilter(section) }
                    )
                )
            }
        }
        return items
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
