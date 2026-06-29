import SwiftUI

struct DaemonView: View {
    private enum SectionAnchor: String, CaseIterable {
        case operatorWorkspace
        case packagingModels
        case operatorPhase
        case serviceLifecycle
        case supervision
        case recoveryPolicy
        case launchAgent
        case launchAgentRunbook
        case nextActions
    }

    @ObservedObject var model: AppModel
    @State private var showOperatorPhase = false
    @State private var showServiceLifecycle = false
    @State private var showSupervision = false
    @State private var showRecoveryPolicy = false
    @State private var showLaunchAgent = true
    @State private var showLaunchAgentRunbook = true
    @State private var showLaunchAgentCurrentStateDetails = false
    @State private var showLaunchAgentRecoveryPreview = false
    @State private var showLaunchAgentStatusDiagnostics = false
    @State private var showLaunchAgentStderrPreview = false
    @State private var showStartupVisibility = false
    @State private var showHandoffSnapshot = false
    @State private var showRunbookProofDiagnostics = false
    @State private var showRunbookPlistPreview = false
    @State private var showOperatorSupportedPath = false
    @State private var showOperatorExitCriteria = false
    @State private var showOperatorReadSurfaces = false
    @State private var showOperatorDecisionAssist = false
    @State private var showOperatorEvidenceDrilldown = false
    @State private var showOperatorNotInScope = false
    @State private var showServiceTargetsDetails = false
    @State private var showServiceAllowedCommands = false
    @State private var showServiceDeferredCommands = false
    @State private var showServiceAppPolicy = false
    @State private var showSupervisionCandidates = false
    @State private var showRecoveryMutatingActions = false
    @State private var showRecoveryControlActions = false
    @State private var showRecoveryFlowDetails = false
    @State private var showPackagingOperatorSurface = false
    @State private var showPackagingCandidates = false
    @State private var showPackagingGuardrails = false

    private struct OperatorWorkspaceItem: Identifiable {
        let id: String
        let anchor: SectionAnchor
        let phaseItem: String
        let title: String
        let status: String
        let tone: StatusTone
        let summary: String
        let detail: String?
        let command: String
        let blockers: [String]
    }

    private struct EvidenceEntry: Identifiable {
        let id: String
        let title: String
        let command: String
        let anchor: SectionAnchor
        let tone: StatusTone
        let snapshot: String
        let detail: String?
    }

    private struct PhaseClosureGateItem: Identifiable {
        let id: String
        let title: String
        let status: String
        let blockers: [String]
        let command: String
        let anchor: SectionAnchor
        let tone: StatusTone
    }

    private struct DecisionAssistItem: Identifiable {
        let id: String
        let title: String
        let summary: String
        let command: String
        let anchor: SectionAnchor
        let tone: StatusTone
    }

    private struct OperatorSummaryRailItem: Identifiable {
        let id: String
        let title: String
        let summary: String
        let badge: String
        let command: String
        let anchor: SectionAnchor
        let tone: StatusTone
    }

    private struct FocusItem: Identifiable {
        let id: String
        let title: String
        let summary: String
        let badge: String
        let tone: StatusTone
        let anchor: SectionAnchor
    }

    private enum DeeperReviewBlock: String, CaseIterable, Identifiable {
        case phaseClosureGates
        case decisionAssist
        case evidenceDrilldown
        case remainingWorkstreams

        var id: String { rawValue }
    }

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    focusSection(proxy: proxy)
                    nextActions
                        .id(SectionAnchor.nextActions)
                    operatorSummaryRail(proxy: proxy)
                    operatorWorkspace(proxy: proxy)
                        .id(SectionAnchor.operatorWorkspace)
                    sectionNavigator(proxy: proxy)
                    launchAgent
                        .id(SectionAnchor.launchAgent)
                    serviceTargets
                    cards
                    operatorPanels
                    operatorPhase
                        .id(SectionAnchor.operatorPhase)
                    packagingModels
                        .id(SectionAnchor.packagingModels)
                    serviceLifecycle
                        .id(SectionAnchor.serviceLifecycle)
                    supervision
                        .id(SectionAnchor.supervision)
                    recoveryPolicy
                        .id(SectionAnchor.recoveryPolicy)
                    launchAgentRunbook
                        .id(SectionAnchor.launchAgentRunbook)
                    startupVisibility
                    handoffSnapshot
                }
                .padding(24)
            }
        }
        .navigationTitle(model.strings.text(.daemon))
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 10) {
            BridgeStatusPanel(model: model, compact: true)
            HStack {
                Button(model.strings.text(.expandAll)) {
                    setAllExpanded(true)
                }
                Button(model.strings.text(.collapseAll)) {
                    setAllExpanded(false)
                }
                Spacer()
                Button(model.strings.text(.exportHandoffNote)) {
                    model.exportDaemonHandoffNote()
                }
                .disabled(model.daemonHandoffExportText() == nil)
            }
        }
    }

    private func operatorSummaryRail(proxy: ScrollViewProxy) -> some View {
        GroupBox(model.strings.text(.operatorSummaryRail)) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.operatorSummaryRailSummary))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack {
                    Spacer()
                    Button(model.strings.text(.copyOperatorSummary)) {
                        model.copyDaemonOperatorSummary()
                    }
                }
                if operatorSummaryRailItems.isEmpty {
                    StateCardView(
                        icon: "rectangle.3.group",
                        title: model.strings.text(.operatorSummaryRail),
                        message: model.daemonSummaryEmptyMessage,
                        tone: .neutral
                        ,
                        badgeText: model.daemonSummaryEmptyBadgeText
                    )
                } else {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 240), spacing: 10)], spacing: 10) {
                        ForEach(operatorSummaryRailPreviewItems) { item in
                            SurfaceCard(emphasis: 0.30) {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack(alignment: .top, spacing: 8) {
                                        CardTitleSummary(title: item.title, summary: item.summary)
                                        Spacer()
                                        StatusBadge(text: item.badge, tone: item.tone)
                                    }
                                    commandActionBlock(
                                        title: item.title,
                                        command: item.command,
                                        anchor: item.anchor,
                                        proxy: proxy
                                    )
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                    }
                    if operatorSummaryRailOverflowCount > 0 {
                        Text(model.strings.moreItemsMessage(operatorSummaryRailOverflowCount))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func sectionNavigator(proxy: ScrollViewProxy) -> some View {
        GroupBox(model.strings.text(.sectionNavigator)) {
            VStack(alignment: .leading, spacing: 8) {
                Text(model.strings.text(.sectionNavigatorSummary))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                if !priorityNavigationItems.isEmpty {
                    navigatorRow(
                        title: model.strings.text(.prioritySections),
                        items: priorityNavigationItems,
                        proxy: proxy
                    )
                }
                if !secondaryNavigationItems.isEmpty {
                    navigatorRow(
                        title: model.strings.text(.otherSections),
                        items: secondaryNavigationItems,
                        proxy: proxy
                    )
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private func navigatorRow(
        title: String,
        items: [(anchor: SectionAnchor, title: String, tone: StatusTone)],
        proxy: ScrollViewProxy
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption.weight(.semibold))
            FlowLayout(items, id: \.anchor, spacing: 8) { item in
                Button {
                    expandSection(item.anchor)
                    withAnimation {
                        proxy.scrollTo(item.anchor, anchor: .top)
                    }
                } label: {
                    StatusBadge(text: item.title, tone: item.tone)
                }
                .buttonStyle(.plain)
                .accessibilityLabel(item.title)
            }
        }
    }

    private func operatorWorkspace(proxy: ScrollViewProxy) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.nextEpicWorkspace))
            Text(model.strings.text(.nextEpicWorkspaceSummary))
                .font(.caption)
                .foregroundStyle(.secondary)
            if operatorWorkspaceItems.isEmpty {
                StateCardView(
                    icon: "square.grid.2x2",
                    title: model.strings.text(.nextEpicWorkspace),
                    message: model.daemonWorkspaceEmptyMessage,
                    tone: .neutral,
                    badgeText: model.daemonWorkspaceEmptyBadgeText,
                    actionTitle: model.toolbarRefreshText,
                    actionEnabled: !model.bridgeRecoveryActionDisabled,
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                operatorWorkspaceOverview
                ForEach(orderedDeeperReviewBlocks) { block in
                    deeperReviewBlock(block, proxy: proxy)
                }
            }
        }
    }

    @ViewBuilder
    private func deeperReviewBlock(_ block: DeeperReviewBlock, proxy: ScrollViewProxy) -> some View {
        switch block {
        case .phaseClosureGates:
            phaseClosureGates(proxy: proxy)
        case .decisionAssist:
            operatorDecisionAssist(proxy: proxy)
        case .evidenceDrilldown:
            operatorEvidenceRail(proxy: proxy)
        case .remainingWorkstreams:
            GroupBox(model.strings.text(.remainingWorkstreams)) {
                VStack(alignment: .leading, spacing: 10) {
                    Text(model.strings.text(.remainingWorkstreamsSummary))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if workspaceDisplayItems.isEmpty {
                        StateCardView(
                            icon: "square.grid.2x2",
                            title: model.strings.text(.remainingWorkstreams),
                            message: model.strings.text(.priorityPathCoversCurrentWorkspace),
                            tone: .neutral
                        )
                    } else {
                        LazyVGrid(columns: [GridItem(.adaptive(minimum: 240), spacing: 12)], spacing: 12) {
                            ForEach(workspaceDisplayPreviewItems) { item in
                                SurfaceCard(emphasis: 0.3) {
                                    VStack(alignment: .leading, spacing: 10) {
                                        HStack(alignment: .top, spacing: 8) {
                                            CardTitleSummary(title: item.title, summary: item.summary)
                                            Spacer()
                                            VStack(alignment: .trailing, spacing: 6) {
                                                if let index = recommendedOrderIndex(for: item.phaseItem) {
                                                    StatusBadge(
                                                        text: "\(model.strings.text(.implementationOrder)) \(index)",
                                                        tone: .neutral
                                                    )
                                                }
                                                StatusBadge(text: item.status, tone: item.tone)
                                            }
                                        }
                                        if let detail = item.detail, !detail.isEmpty {
                                            Text(detail)
                                                .font(.caption)
                                                .foregroundStyle(.secondary)
                                        }
                                        if !item.blockers.isEmpty {
                                            VStack(alignment: .leading, spacing: 4) {
                                                Text(model.strings.text(.blockedBy))
                                                    .font(.caption.weight(.semibold))
                                                if let primaryBlocker = item.blockers.first {
                                                    Text(model.strings.tokenLabel(primaryBlocker))
                                                        .font(.caption)
                                                        .foregroundStyle(.secondary)
                                                }
                                                if item.blockers.count > 1 {
                                                    Text("\(model.strings.text(.additionalBlockers)): \(item.blockers.count - 1)")
                                                        .font(.caption2)
                                                        .foregroundStyle(.secondary)
                                                }
                                            }
                                        }
                                        commandActionBlock(
                                            title: item.title,
                                            command: item.command,
                                            anchor: item.anchor,
                                            proxy: proxy
                                        )
                                    }
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                }
                            }
                        }
                        if workspaceDisplayOverflowCount > 0 {
                            Text(model.strings.moreItemsMessage(workspaceDisplayOverflowCount))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
    }

    private func phaseClosureGates(proxy: ScrollViewProxy) -> some View {
        GroupBox(model.strings.text(.phaseClosureGates)) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.phaseClosureGatesSummary))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack {
                    Spacer()
                    Button(model.strings.text(.copyPhaseGates)) {
                        model.copyDaemonPhaseGates()
                    }
                    .disabled(model.daemonPhaseGatesClipboardText() == nil)
                }
                if phaseClosureGateItems.isEmpty {
                    StateCardView(
                        icon: "checklist",
                        title: model.strings.text(.phaseClosureGates),
                        message: model.strings.text(.noPriorityActions),
                        tone: .neutral
                    )
                } else {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 240), spacing: 10)], spacing: 10) {
                        ForEach(orderedPhaseClosureGateItems) { item in
                            SurfaceCard(emphasis: 0.26) {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack(alignment: .top, spacing: 8) {
                                        Text(item.title)
                                            .font(.headline)
                                        Spacer()
                                        StatusBadge(text: item.status, tone: item.tone)
                                    }
                                    if let primaryBlocker = item.blockers.first {
                                        Text("\(model.strings.text(.blockedBy)): \(model.strings.tokenLabel(primaryBlocker))")
                                            .font(.subheadline)
                                            .foregroundStyle(.secondary)
                                    } else {
                                        Text(model.strings.text(.noPriorityActions))
                                            .font(.subheadline)
                                            .foregroundStyle(.secondary)
                                    }
                                    if item.blockers.count > 1 {
                                        Text(item.blockers.dropFirst().map(model.strings.tokenLabel).joined(separator: " · "))
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                    commandActionBlock(
                                        title: item.title,
                                        command: item.command,
                                        anchor: item.anchor,
                                        proxy: proxy
                                    )
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func operatorDecisionAssist(proxy: ScrollViewProxy) -> some View {
        GroupBox(model.strings.text(.suggestedAction)) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.decisionAssist))
                    .font(.caption.weight(.semibold))
                Text(model.strings.text(.decisionAssistSummary))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack {
                    Spacer()
                    Button(model.strings.text(.copySuggestedActions)) {
                        model.copyDaemonSuggestedActions()
                    }
                    .disabled(model.daemonSuggestedActionsClipboardText() == nil)
                }
                if decisionAssistItems.isEmpty {
                    StateCardView(
                        icon: "lightbulb",
                        title: model.strings.text(.suggestedAction),
                        message: model.strings.text(.noPriorityActions),
                        tone: .neutral
                    )
                } else {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 240), spacing: 10)], spacing: 10) {
                        ForEach(decisionAssistPreviewItems) { item in
                            SurfaceCard(emphasis: 0.28) {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack(alignment: .top, spacing: 8) {
                                        Text(item.title)
                                            .font(.headline)
                                        Spacer()
                                        StatusBadge(text: model.strings.text(.suggestedAction), tone: item.tone)
                                    }
                                    Text(item.summary)
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    commandActionBlock(
                                        title: item.title,
                                        command: item.command,
                                        anchor: item.anchor,
                                        proxy: proxy
                                    )
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                    }
                    if decisionAssistOverflowCount > 0 {
                        Text(model.strings.moreItemsMessage(decisionAssistOverflowCount))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func operatorEvidenceRail(proxy: ScrollViewProxy) -> some View {
        GroupBox(model.strings.text(.readSurfaces)) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.evidenceDrilldown))
                    .font(.caption.weight(.semibold))
                Text(model.strings.text(.evidenceDrilldownSummary))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack {
                    Spacer()
                    Button(model.strings.text(.copyReadSurfaces)) {
                        model.copyDaemonReadSurfaces()
                    }
                    .disabled(model.daemonReadSurfacesClipboardText() == nil)
                }
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 240), spacing: 10)], spacing: 10) {
                    ForEach(evidencePreviewItems) { entry in
                        SurfaceCard(emphasis: 0.22) {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack(alignment: .top, spacing: 8) {
                                    CardTitleSummary(title: entry.title, summary: entry.snapshot)
                                    Spacer()
                                    StatusBadge(text: model.strings.text(.readSurfaces), tone: entry.tone)
                                }
                                if let detail = entry.detail, !detail.isEmpty {
                                    Text(detail)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                commandActionBlock(
                                    title: entry.title,
                                    command: entry.command,
                                    anchor: entry.anchor,
                                    proxy: proxy
                                )
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }
                if evidenceOverflowCount > 0 {
                    Text(model.strings.moreItemsMessage(evidenceOverflowCount))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var operatorWorkspaceOverview: some View {
        GroupBox(model.strings.text(.operatorPhase)) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.operatorWorkspaceCompactSummary))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack(alignment: .top, spacing: 8) {
                    StatusBadge(
                        text: model.daemonState?.operatorPhaseSummary.phaseReadiness.map(model.strings.tokenLabel) ?? model.strings.text(.none),
                        tone: model.daemonState?.operatorPhaseSummary.phaseReadiness.map(model.strings.tone(forToken:)) ?? .neutral
                    )
                    StatusBadge(
                        text: model.daemonState?.operatorPhaseSummary.phaseStatus.map(model.strings.tokenLabel) ?? model.strings.text(.none),
                        tone: .neutral
                    )
                    Spacer()
                    Button(model.strings.text(.copyCommand)) {
                        model.copyToClipboard(
                            "sayane app daemon-operator-phase-status --json",
                            message: model.strings.copiedCommandMessage(context: model.strings.text(.operatorPhase))
                        )
                    }
                }
                if let checklist = phaseChecklistItems, !checklist.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(model.strings.text(.phaseChecklist))
                            .font(.caption.weight(.semibold))
                        ForEach(Array(checklist.prefix(3).enumerated()), id: \.offset) { _, item in
                            HStack(alignment: .top, spacing: 8) {
                                StatusBadge(text: model.strings.tokenLabel(item.status), tone: model.strings.tone(forToken: item.status))
                                Text(model.strings.summaryCardLabel(item.name))
                                    .font(.caption)
                            }
                        }
                    }
                }
                if !implementationOrderItems.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(model.strings.text(.implementationOrder))
                            .font(.caption.weight(.semibold))
                        FlowLayout(Array(implementationOrderItems.enumerated()), id: \.offset, spacing: 6) { entry in
                            StatusBadge(
                                text: "\(entry.offset + 1). \(model.strings.summaryCardLabel(entry.element))",
                                tone: .neutral
                            )
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private func commandActionBlock(
        title: String,
        command: String,
        anchor: SectionAnchor,
        proxy: ScrollViewProxy
    ) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(model.strings.text(.nextCommand))
                .font(.caption.weight(.semibold))
            CommandRowView(
                command: command,
                font: .system(.caption, design: .monospaced),
                foregroundColor: .secondary,
                lineLimit: 2
            )
        }
        HStack {
            Button(model.strings.text(.openSection)) {
                expandSection(anchor)
                withAnimation {
                    proxy.scrollTo(anchor, anchor: .top)
                }
            }
            Button(model.strings.text(.copyCommand)) {
                model.copyToClipboard(
                    command,
                    message: model.strings.copiedCommandMessage(context: title)
                )
            }
        }
    }

    private func focusSection(proxy: ScrollViewProxy) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.startHere))
            if daemonFocusItems.isEmpty {
                StateCardView(
                    icon: "scope",
                    title: model.strings.text(.startHere),
                    message: model.strings.text(.noPriorityActions),
                    tone: .neutral,
                    badgeText: model.strings.text(.healthySignals),
                    actionTitle: model.toolbarRefreshText,
                    actionEnabled: !model.bridgeRecoveryActionDisabled,
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 250), spacing: 12)], spacing: 12) {
                    ForEach(daemonFocusItems) { item in
                        Button {
                            expandSection(item.anchor)
                            withAnimation {
                                proxy.scrollTo(item.anchor, anchor: .top)
                            }
                        } label: {
                            SurfaceCard(emphasis: 0.34) {
                                HStack(alignment: .top, spacing: 12) {
                                    StatusBadge(text: item.badge, tone: item.tone)
                                    CardTitleSummary(title: item.title, summary: item.summary)
                                    Spacer()
                                    Image(systemName: "arrow.right.circle.fill")
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("\(item.badge) \(item.title) \(item.summary)")
                    }
                }
            }
        }
    }

    private var cards: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.summaryCards))
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 180))], spacing: 12) {
                ForEach(model.daemonState?.summaryCards ?? []) { card in
                    SurfaceCard {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.summaryCardLabel(card.key)).font(.caption).foregroundStyle(.secondary)
                            SummaryCardValueView(strings: model.strings, card: card)
                        }
                    }
                }
            }
        }
    }

    private var operatorPanels: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.status))
            Text(model.strings.text(.statusSectionSummary))
                .font(.caption)
                .foregroundStyle(.secondary)
            ForEach(orderedOperatorPanels) { panel in
                GroupBox(model.strings.operatorPanelLabel(panel.panel)) {
                    VStack(alignment: .leading, spacing: 6) {
                        if let status = panel.status {
                            HStack {
                                Text("\(model.strings.fieldLabel("status")):")
                                StatusBadge(text: model.strings.tokenLabel(status), tone: model.strings.tone(forToken: status))
                            }
                        }
                        if let highlights = panel.highlights {
                            FlowLayout(orderedHighlights(highlights), id: \.self, spacing: 6) { highlight in
                                StatusBadge(text: model.strings.tokenLabel(highlight), tone: model.strings.tone(forToken: highlight))
                            }
                        }
                        if let commands = panel.commands, !commands.isEmpty {
                            ForEach(Array(commands.prefix(2)), id: \.self) { command in
                                commandRow(command)
                            }
                            if commands.count > 2 {
                                Text(model.strings.moreItemsMessage(commands.count - 2))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        if let deferred = panel.deferredCommands, !deferred.isEmpty {
                            Text("\(model.strings.text(.deferredCommands)): \(deferred.prefix(2).joined(separator: ", "))")
                            if deferred.count > 2 {
                                Text(model.strings.moreItemsMessage(deferred.count - 2))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        if let flow = panel.recommendedFlow, !flow.isEmpty {
                            Text("\(model.strings.fieldLabel("flow")): \(flow.prefix(2).joined(separator: " → "))")
                            if flow.count > 2 {
                                Text(model.strings.moreItemsMessage(flow.count - 2))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
    }

    private var orderedOperatorPanels: [OperatorPanel] {
        (model.daemonState?.operatorPanels ?? []).sorted { lhs, rhs in
            let lhsPriority = model.strings.operatorPanelPriority(lhs.panel)
            let rhsPriority = model.strings.operatorPanelPriority(rhs.panel)
            if lhsPriority != rhsPriority {
                return lhsPriority < rhsPriority
            }
            return model.strings.operatorPanelLabel(lhs.panel) < model.strings.operatorPanelLabel(rhs.panel)
        }
    }

    private func orderedHighlights(_ highlights: [String]) -> [String] {
        highlights.sorted { lhs, rhs in
            let lhsPriority = model.strings.highlightPriority(lhs)
            let rhsPriority = model.strings.highlightPriority(rhs)
            if lhsPriority != rhsPriority {
                return lhsPriority < rhsPriority
            }
            return model.strings.tokenLabel(lhs) < model.strings.tokenLabel(rhs)
        }
    }

    private var operatorPhase: some View {
        expandableSection(
            title: model.strings.text(.operatorPhase),
            summary: operatorPhaseSectionSummary,
            isExpanded: $showOperatorPhase
        ) {
            if let summary = model.daemonState?.operatorPhaseSummary {
                GroupBox(model.strings.text(.summaryCards)) {
                    VStack(alignment: .leading, spacing: 6) {
                        DetailLabelValueRow(
                            label: model.strings.fieldLabel("phase"),
                            value: summary.phase.map(model.strings.tokenLabel) ?? model.strings.text(.none)
                        )
                        if let phaseStatus = summary.phaseStatus {
                            DetailBadgeRow(
                                label: model.strings.fieldLabel("status"),
                                badgeText: model.strings.tokenLabel(phaseStatus),
                                tone: model.strings.tone(forToken: phaseStatus)
                            )
                        } else {
                            DetailLabelValueRow(label: model.strings.fieldLabel("status"), value: model.strings.text(.none))
                        }
                        if let readiness = summary.phaseReadiness {
                            DetailBadgeRow(
                                label: model.strings.fieldLabel("readiness"),
                                badgeText: model.strings.tokenLabel(readiness),
                                tone: model.strings.tone(forToken: readiness)
                            )
                        } else {
                            DetailLabelValueRow(label: model.strings.fieldLabel("readiness"), value: model.strings.text(.none))
                        }
                        BulletListView(values: summary.blockingReasons)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            if let details = model.daemonState?.operatorPhaseDetails {
                compactDisclosureSection(
                    title: model.strings.text(.supportedPath),
                    isExpanded: $showOperatorSupportedPath
                ) {
                    VStack(alignment: .leading, spacing: 6) {
                        if let startupCommand = details.currentSupportedOperatorPath.startupCommandText,
                           !startupCommand.isEmpty {
                            Text(model.strings.text(.startupCommand))
                                .font(.caption.weight(.semibold))
                            commandRow(startupCommand)
                            StartupShortcutButtons(model: model, command: startupCommand)
                        } else {
                            Text(model.strings.text(.none))
                                .font(.subheadline.weight(.semibold))
                        }
                        if let primaryOperatorUI = details.currentSupportedOperatorPath.primaryOperatorUI,
                           !primaryOperatorUI.isEmpty {
                            DetailLabelValueRow(
                                label: model.strings.text(.primaryOperatorUI),
                                value: model.strings.tokenLabel(primaryOperatorUI)
                            )
                        }
                        if let recommendedLauncher = details.currentSupportedOperatorPath.recommendedLauncher,
                           !recommendedLauncher.isEmpty {
                            Text(model.strings.text(.recommendedLauncher))
                                .font(.caption.weight(.semibold))
                            commandRow(recommendedLauncher)
                        }
                        if details.currentSupportedOperatorPath.bootstrapUI != nil {
                            DebugCompatibilityDisclosure(model: model) {
                                VStack(alignment: .leading, spacing: 6) {
                                    DebugShellShortcutButtons(model: model)
                                }
                            }
                        }
                        if let localOnly = details.currentSupportedOperatorPath.localOnly {
                            DetailLabelValueRow(
                                label: model.strings.text(.localOnly),
                                value: model.strings.booleanValueLabel(localOnly)
                            )
                        }
                        if !details.currentSupportedOperatorPath.notes.isEmpty {
                            Text(model.strings.text(.notes))
                                .font(.caption.weight(.semibold))
                            BulletListView(values: Array(details.currentSupportedOperatorPath.notes.prefix(2)))
                            if details.currentSupportedOperatorPath.notes.count > 2 {
                                Text(model.strings.moreItemsMessage(details.currentSupportedOperatorPath.notes.count - 2))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        if !details.workstreams.isEmpty {
                            Text(model.strings.text(.workstreams))
                                .font(.caption.weight(.semibold))
                            BulletListView(
                                values: Array(details.workstreams.prefix(3)).map {
                                    "\(model.strings.summaryCardLabel($0.name)): \($0.status.map(model.strings.tokenLabel) ?? "-")"
                                }
                            )
                            if details.workstreams.count > 3 {
                                Text(model.strings.moreItemsMessage(details.workstreams.count - 3))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
                compactDisclosureSection(
                    title: model.strings.text(.exitCriteria),
                    isExpanded: $showOperatorExitCriteria
                ) {
                    VStack(alignment: .leading, spacing: 6) {
                        BulletListView(values: Array(details.exitCriteria.prefix(4)))
                        if details.exitCriteria.count > 4 {
                            Text(model.strings.moreItemsMessage(details.exitCriteria.count - 4))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                compactDisclosureSection(
                    title: model.strings.text(.readSurfaces),
                    isExpanded: $showOperatorReadSurfaces
                ) {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(Array(details.readSurfaces.prefix(3)), id: \.self) { surface in
                            commandRow(surface)
                        }
                        if details.readSurfaces.count > 3 {
                            Text(model.strings.moreItemsMessage(details.readSurfaces.count - 3))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                if let decisionAssist = details.decisionAssist, !decisionAssist.isEmpty {
                    compactDisclosureSection(
                        title: model.strings.text(.decisionAssist),
                        isExpanded: $showOperatorDecisionAssist
                    ) {
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(Array(decisionAssist.prefix(4))) { item in
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(model.strings.summaryCardLabel(item.topic))
                                        .font(.caption.weight(.semibold))
                                    Text(item.summary)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                    commandRow(item.command)
                                }
                            }
                        }
                    }
                }
                if let closureEvidence = details.closureEvidence, !closureEvidence.isEmpty {
                    compactDisclosureSection(
                        title: model.strings.text(.evidenceDrilldown),
                        isExpanded: $showOperatorEvidenceDrilldown
                    ) {
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(Array(closureEvidence.prefix(4))) { item in
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(model.strings.summaryCardLabel(item.surface))
                                        .font(.caption.weight(.semibold))
                                    Text(item.confirms)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                    commandRow(item.command)
                                }
                            }
                        }
                    }
                }
                compactDisclosureSection(
                    title: model.strings.text(.notInScope),
                    isExpanded: $showOperatorNotInScope
                ) {
                    VStack(alignment: .leading, spacing: 6) {
                        BulletListView(values: Array(details.notInScope.prefix(4)))
                        if details.notInScope.count > 4 {
                            Text(model.strings.moreItemsMessage(details.notInScope.count - 4))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
    }

    private var startupVisibility: some View {
        compactDisclosureSection(
            title: model.strings.text(.startupVisibility),
            isExpanded: $showStartupVisibility
        ) {
            VStack(alignment: .leading, spacing: 10) {
                if let startup = model.daemonState?.operatorPhaseStatus?["current_supported_operator_path"]?.objectValue {
                    if let command = startup["startup_command_text"]?.stringValue {
                        Text(model.strings.text(.startupCommand)).bold()
                        commandRow(command)
                        StartupShortcutButtons(model: model, command: command)
                    }
                    if startup["bootstrap_ui"]?.stringValue != nil {
                        DebugCompatibilityDisclosure(model: model) {
                            VStack(alignment: .leading, spacing: 6) {
                                DebugShellShortcutButtons(model: model)
                            }
                        }
                    }
                    if let localOnly = startup["local_only"]?.boolValue {
                        DetailLabelValueRow(
                            label: model.strings.text(.localOnly),
                            value: model.strings.booleanValueLabel(localOnly)
                        )
                    }
                    stringList(
                        title: model.strings.text(.notes),
                        values: startup["notes"]?.arrayValue?.compactMap(\.stringValue) ?? []
                    )
                }
                if let checklist = model.daemonState?.operatorPhaseStatus?["phase_closure_checklist"]?.arrayValue {
                    Text(model.strings.text(.phaseChecklist)).bold()
                    ForEach(Array(checklist.enumerated()), id: \.offset) { _, value in
                        if let object = value.objectValue {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(object["item"]?.stringValue ?? model.strings.text(.none)).bold()
                                if let status = object["status"]?.stringValue {
                                    DetailBadgeRow(
                                        label: model.strings.text(.statusValue),
                                        badgeText: model.strings.tokenLabel(status),
                                        tone: model.strings.tone(forToken: status)
                                    )
                                }
                                stringList(
                                    title: model.strings.text(.blockedBy),
                                    values: object["blocking_reasons"]?.arrayValue?.compactMap(\.stringValue) ?? []
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    private var handoffSnapshot: some View {
        compactDisclosureSection(
            title: model.strings.text(.handoffSnapshot),
            isExpanded: $showHandoffSnapshot
        ) {
            VStack(alignment: .leading, spacing: 10) {
                if let workstreams = model.daemonState?.operatorPhaseStatus?["workstreams"]?.arrayValue {
                    Text(model.strings.text(.workstreams)).bold()
                    ForEach(Array(workstreams.enumerated()), id: \.offset) { _, value in
                        if let object = value.objectValue {
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text(object["name"]?.stringValue ?? model.strings.text(.none)).bold()
                                    Spacer()
                                    if let status = object["status"]?.stringValue {
                                        StatusBadge(text: model.strings.tokenLabel(status), tone: model.strings.tone(forToken: status))
                                    }
                                }
                                if let currentState = object["current_state"]?.stringValue {
                                    StatusBadge(text: model.strings.tokenLabel(currentState), tone: model.strings.tone(forToken: currentState))
                                } else if let currentTarget = object["current_target"]?.stringValue {
                                    StatusBadge(text: model.strings.tokenLabel(currentTarget), tone: model.strings.tone(forToken: currentTarget))
                                } else if let backgroundStatus = object["background_status"]?.stringValue {
                                    StatusBadge(text: model.strings.tokenLabel(backgroundStatus), tone: model.strings.tone(forToken: backgroundStatus))
                                } else if let consentModel = object["consent_model"]?.stringValue {
                                    StatusBadge(text: model.strings.tokenLabel(consentModel), tone: model.strings.tone(forToken: consentModel))
                                }
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.vertical, 4)
                        }
                    }
                }
                stringList(
                    title: model.strings.text(.implementationOrder),
                    values: model.daemonState?.operatorPhaseDetails.recommendedImplementationOrder ?? []
                )
            }
        }
    }

    private var serviceTargets: some View {
        GroupBox(model.strings.text(.serviceTargets)) {
            VStack(alignment: .leading, spacing: 6) {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 220), spacing: 10)], spacing: 10) {
                    SurfaceCard(emphasis: 0.22) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.text(.currentPlatform))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            StatusBadge(
                                text: model.daemonState?.serviceTargetSummary.currentPlatform.map(model.strings.tokenLabel) ?? model.strings.text(.none),
                                tone: .neutral
                            )
                        }
                    }
                    SurfaceCard(emphasis: 0.22) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.text(.recommended))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            StatusBadge(
                                text: model.daemonState?.serviceTargetSummary.recommendedTarget.map(model.strings.tokenLabel) ?? model.strings.text(.none),
                                tone: .positive
                            )
                        }
                    }
                    SurfaceCard(emphasis: 0.22) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.text(.platformTargets))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text("\((model.daemonState?.serviceTargetSummary.targets.count) ?? 0)")
                                .font(.headline)
                        }
                    }
                }
                compactDisclosureSection(
                    title: model.strings.text(.platformTargets),
                    isExpanded: $showServiceTargetsDetails
                ) {
                    if let policyGates = model.daemonState?.serviceTargetsStatus?["policy_gates"]?.objectValue {
                        stringList(title: model.strings.text(.policyGates), values: policyGates.map { "\(model.strings.summaryCardLabel($0)): \($1.boolValue.map(model.strings.booleanValueLabel) ?? $1.displayText)" }.sorted())
                    }
                    ForEach(model.daemonState?.serviceTargetSummary.targets ?? []) { target in
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text("• \(model.strings.tokenLabel(target.target)):")
                                if let status = target.status {
                                    StatusBadge(text: model.strings.tokenLabel(status), tone: model.strings.tone(forToken: status))
                                } else {
                                    Text("-")
                                }
                            }
                            if let notes = target.notes, !notes.isEmpty {
                                VStack(alignment: .leading, spacing: 2) {
                                    BulletListView(values: notes.map { "  \($0)" })
                                }
                                .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var serviceLifecycle: some View {
        expandableSection(
            title: model.strings.text(.serviceLifecycle),
            summary: serviceLifecycleSummary,
            isExpanded: $showServiceLifecycle
        ) {
            VStack(alignment: .leading, spacing: 10) {
                if let allowedCommands = model.daemonState?.serviceControlBoundary?["control_plane"]?.objectValue?["allowed_commands"]?.arrayValue {
                    compactDisclosureSection(
                        title: model.strings.text(.allowedCommands),
                        isExpanded: $showServiceAllowedCommands
                    ) {
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(Array(allowedCommands.enumerated()), id: \.offset) { _, value in
                                if let command = value.objectValue?["command"]?.stringValue {
                                    commandRow(command)
                                }
                            }
                        }
                    }
                }
                stringList(
                    title: model.strings.text(.recoveryPolicy),
                    values: model.daemonState?.serviceControlBoundary?["control_plane"]?.objectValue?["recovery_policy"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                if let deferredCommands = model.daemonState?.serviceControlBoundary?["service_plane"]?.objectValue?["deferred_commands"]?.arrayValue?.compactMap(\.stringValue),
                   !deferredCommands.isEmpty {
                    compactDisclosureSection(
                        title: model.strings.text(.deferredCommands),
                        isExpanded: $showServiceDeferredCommands
                    ) {
                        VStack(alignment: .leading, spacing: 6) {
                            FlowLayout(deferredCommands, id: \.self, spacing: 6) { command in
                                StatusBadge(text: model.strings.tokenLabel(command), tone: .caution)
                            }
                        }
                    }
                }
                stringList(
                    title: model.strings.text(.platformTargets),
                    values: model.daemonState?.serviceControlBoundary?["service_plane"]?.objectValue?["platform_targets"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                if let lifecycle = model.daemonState?.serviceControlBoundary?["service_plane"]?.objectValue?["lifecycle_operations"]?.arrayValue {
                    ForEach(Array(lifecycle.enumerated()), id: \.offset) { _, value in
                        if let object = value.objectValue {
                            SurfaceCard(emphasis: 0.25) {
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text(object["operation"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)).bold()
                                        Spacer()
                                        if let status = object["status"]?.stringValue {
                                            StatusBadge(text: model.strings.tokenLabel(status), tone: model.strings.tone(forToken: status))
                                        }
                                    }
                                    if let command = object["command"]?.stringValue {
                                        commandRow(command)
                                    }
                                    stringList(
                                        title: model.strings.text(.platformScope),
                                        values: object["platform_scope"]?.arrayValue?.compactMap(\.stringValue) ?? []
                                    )
                                    if let rollback = object["rollback_required"]?.boolValue {
                                        DetailLabelValueRow(
                                            label: model.strings.text(.rollbackRequired),
                                            value: model.strings.booleanValueLabel(rollback)
                                        )
                                    }
                                    if let policy = object["policy_required"]?.boolValue {
                                        DetailLabelValueRow(
                                            label: model.strings.text(.policyRequired),
                                            value: model.strings.booleanValueLabel(policy)
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
                if let appPolicy = model.daemonState?.serviceControlBoundary?["app_ui_policy"]?.objectValue {
                    compactDisclosureSection(
                        title: model.strings.text(.appUIPolicy),
                        isExpanded: $showServiceAppPolicy
                    ) {
                        VStack(alignment: .leading, spacing: 8) {
                            stringList(title: model.strings.text(.allowedReads), values: appPolicy["allowed_reads"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                            stringList(title: model.strings.text(.allowedWrites), values: appPolicy["allowed_writes"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                            stringList(title: model.strings.text(.allowedControlExposure), values: appPolicy["allowed_control_exposure"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                            stringList(title: model.strings.text(.forbiddenExposure), values: appPolicy["forbidden_control_exposure"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                        }
                    }
                }
                stringList(
                    title: model.strings.text(.governingRules),
                    values: model.daemonState?.serviceControlBoundary?["governing_rules"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
            }
        }
    }

    private var packagingModels: some View {
        GroupBox(model.strings.text(.packagingModels)) {
            VStack(alignment: .leading, spacing: 10) {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 220), spacing: 10)], spacing: 10) {
                    SurfaceCard(emphasis: 0.22) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.text(.currentValue))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            if let current = model.daemonState?.packagingStatus?["packaging_model"]?.stringValue {
                                StatusBadge(
                                    text: model.strings.tokenLabel(current),
                                    tone: model.strings.tone(forToken: current)
                                )
                            } else {
                                Text(model.strings.text(.none))
                                    .font(.headline)
                            }
                        }
                    }
                    SurfaceCard(emphasis: 0.22) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.text(.primaryOperatorUI))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text(
                                model.daemonState?.packagingStatus?["operator_surface"]?.objectValue?["primary_ui"]?.stringValue.map(model.strings.tokenLabel)
                                ?? model.strings.text(.none)
                            )
                            .font(.headline)
                        }
                    }
                    SurfaceCard(emphasis: 0.22) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.text(.packagingModels))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text("\(model.daemonState?.packagingStatus?["packaging_decision"]?.objectValue?["candidate_models"]?.arrayValue?.count ?? 0)")
                                .font(.headline)
                        }
                    }
                }
                if let operatorSurface = model.daemonState?.packagingStatus?["operator_surface"]?.objectValue {
                    compactDisclosureSection(
                        title: model.strings.text(.operatorSurfaceNotes),
                        isExpanded: $showPackagingOperatorSurface
                    ) {
                        if let primaryUI = operatorSurface["primary_ui"]?.stringValue {
                            DetailLabelValueRow(
                                label: model.strings.text(.primaryOperatorUI),
                                value: model.strings.tokenLabel(primaryUI)
                            )
                        }
                        if let recommendedLauncher = operatorSurface["recommended_launcher"]?.objectValue?["command_text"]?.stringValue,
                           !recommendedLauncher.isEmpty {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(model.strings.text(.recommendedLauncher))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                commandRow(recommendedLauncher)
                                StartupShortcutButtons(model: model, command: recommendedLauncher)
                            }
                        }
                        stringList(
                            title: model.strings.text(.operatorSurfaceNotes),
                            values: operatorSurface["notes"]?.arrayValue?.compactMap(\.stringValue) ?? []
                        )
                    }
                }
                if let candidates = model.daemonState?.packagingStatus?["packaging_decision"]?.objectValue?["candidate_models"]?.arrayValue {
                    compactDisclosureSection(
                        title: model.strings.text(.packagingModels),
                        isExpanded: $showPackagingCandidates
                    ) {
                        ForEach(Array(candidates.enumerated()), id: \.offset) { _, value in
                            if let object = value.objectValue {
                                SurfaceCard(emphasis: 0.25) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        HStack {
                                            Text(object["model"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)).bold()
                                            Spacer()
                                            if let status = object["status"]?.stringValue {
                                                StatusBadge(text: model.strings.tokenLabel(status), tone: model.strings.tone(forToken: status))
                                            }
                                        }
                                        if let operatorValue = object["operator_value"]?.stringValue {
                                            Text(operatorValue).foregroundStyle(.secondary)
                                        }
                                        stringList(title: model.strings.text(.blockedBy), values: object["blocked_by"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                                    }
                                }
                            }
                        }
                    }
                }
                compactDisclosureSection(
                    title: model.strings.text(.guardrails),
                    isExpanded: $showPackagingGuardrails
                ) {
                    stringList(
                        title: model.strings.text(.guardrails),
                        values: model.daemonState?.packagingStatus?["packaging_decision"]?.objectValue?["decision_guardrails"]?.arrayValue?.compactMap(\.stringValue) ?? []
                    )
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var supervision: some View {
        expandableSection(
            title: model.strings.text(.supervision),
            summary: supervisionSummary,
            isExpanded: $showSupervision
        ) {
            VStack(alignment: .leading, spacing: 10) {
                if let mode = model.daemonState?.supervisionStatus?["supervision_mode"]?.stringValue {
                    DetailBadgeRow(
                        label: model.strings.text(.mode),
                        badgeText: model.strings.tokenLabel(mode),
                        tone: model.strings.tone(forToken: mode)
                    )
                }
                stringList(
                    title: model.strings.text(.passiveVisibility),
                    values: model.daemonState?.supervisionStatus?["passive_visibility"]?.objectValue?["surfaces"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                stringList(
                    title: model.strings.text(.activeSupervision),
                    values: model.daemonState?.supervisionStatus?["active_supervision"]?.objectValue?["allowed_actions"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                stringList(
                    title: model.strings.text(.startupVisibility),
                    values: model.daemonState?.supervisionStatus?["background_surfaces"]?.objectValue?["deferred_topics"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                if let candidates = model.daemonState?.supervisionStatus?["background_surfaces"]?.objectValue?["candidate_surfaces"]?.arrayValue {
                    compactDisclosureSection(
                        title: model.strings.text(.backgroundSurfaces),
                        isExpanded: $showSupervisionCandidates
                    ) {
                        ForEach(Array(candidates.enumerated()), id: \.offset) { _, value in
                            if let object = value.objectValue {
                                SurfaceCard(emphasis: 0.25) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        HStack {
                                            Text(object["surface"]?.stringValue ?? model.strings.text(.none)).bold()
                                            Spacer()
                                            if let status = object["status"]?.stringValue {
                                                StatusBadge(text: model.strings.tokenLabel(status), tone: model.strings.tone(forToken: status))
                                            }
                                        }
                                        if let operatorValue = object["operator_value"]?.stringValue {
                                            DetailLabelValueRow(
                                                label: model.strings.text(.operatorValue),
                                                value: operatorValue
                                            )
                                        }
                                        stringList(
                                            title: model.strings.text(.platformScope),
                                            values: object["platform_scope"]?.arrayValue?.compactMap(\.stringValue) ?? []
                                        )
                                        stringList(title: model.strings.text(.blockedBy), values: object["forbidden_capabilities"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                                    }
                                }
                            }
                        }
                    }
                }
                stringList(
                    title: model.strings.text(.recoveryFlow),
                    values: model.daemonState?.supervisionStatus?["recovery_entrypoints"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                stringList(
                    title: model.strings.text(.guardrails),
                    values: model.daemonState?.supervisionStatus?["ux_guardrails"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
            }
        }
    }

    private var recoveryPolicy: some View {
        expandableSection(
            title: model.strings.text(.recoveryPolicy),
            summary: recoveryPolicySummary,
            isExpanded: $showRecoveryPolicy
        ) {
            VStack(alignment: .leading, spacing: 10) {
                if let consent = model.daemonState?.recoveryConsentStatus?["consent_model"]?.stringValue {
                    DetailBadgeRow(
                        label: model.strings.text(.consent),
                        badgeText: model.strings.tokenLabel(consent),
                        tone: model.strings.tone(forToken: consent)
                    )
                }
                if let recovery = model.daemonState?.recoveryConsentStatus?["recovery_model"]?.stringValue {
                    DetailBadgeRow(
                        label: model.strings.text(.recovery),
                        badgeText: model.strings.tokenLabel(recovery),
                        tone: model.strings.tone(forToken: recovery)
                    )
                }
                stringList(
                    title: model.strings.text(.allowedCommands),
                    values: model.daemonState?.recoveryConsentStatus?["non_mutating_diagnostics"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                if let mutatingActions = model.daemonState?.recoveryConsentStatus?["mutating_recovery_actions"]?.arrayValue {
                    compactDisclosureSection(
                        title: model.strings.text(.recoverActions),
                        isExpanded: $showRecoveryMutatingActions
                    ) {
                        ForEach(Array(mutatingActions.enumerated()), id: \.offset) { _, value in
                            if let object = value.objectValue, let command = object["command"]?.stringValue {
                                SurfaceCard(emphasis: 0.25) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        HStack {
                                            StatusBadge(text: model.strings.text(.consent), tone: .critical)
                                            Spacer()
                                        }
                                        commandRow(command)
                                        if let scope = object["scope"]?.stringValue {
                                            DetailLabelValueRow(
                                                label: model.strings.text(.scope),
                                                value: scope
                                            )
                                        }
                                        if let consentRequired = object["consent_required"]?.boolValue {
                                            DetailLabelValueRow(
                                                label: model.strings.text(.policyRequired),
                                                value: model.strings.booleanValueLabel(consentRequired)
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                if let controlActions = model.daemonState?.recoveryConsentStatus?["control_recovery_actions"]?.arrayValue {
                    compactDisclosureSection(
                        title: model.strings.text(.activeSupervision),
                        isExpanded: $showRecoveryControlActions
                    ) {
                        ForEach(Array(controlActions.enumerated()), id: \.offset) { _, value in
                            if let object = value.objectValue, let command = object["command"]?.stringValue {
                                SurfaceCard(emphasis: 0.25) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        HStack {
                                            StatusBadge(text: model.strings.text(.suggestedAction), tone: .caution)
                                            Spacer()
                                        }
                                        commandRow(command)
                                        stringList(title: model.strings.text(.notes), values: object["notes"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                                    }
                                }
                            }
                        }
                    }
                }
                compactDisclosureSection(
                    title: model.strings.text(.recoveryFlow),
                    isExpanded: $showRecoveryFlowDetails
                ) {
                    VStack(alignment: .leading, spacing: 8) {
                        stringList(
                            title: model.strings.text(.recoveryFlow),
                            values: model.daemonState?.recoveryConsentStatus?["recommended_recovery_flow"]?.arrayValue?.compactMap(\.stringValue) ?? []
                        )
                        stringList(
                            title: model.strings.text(.guardrails),
                            values: model.daemonState?.recoveryConsentStatus?["app_ui_guardrails"]?.arrayValue?.compactMap(\.stringValue) ?? []
                        )
                    }
                }
            }
        }
    }

    private var launchAgent: some View {
        expandableSection(
            title: model.strings.text(.launchAgent),
            summary: launchAgentSummaryText,
            isExpanded: $showLaunchAgent
        ) {
            VStack(alignment: .leading, spacing: 8) {
                GroupBox(model.strings.text(.launchAgentFocus)) {
                    VStack(alignment: .leading, spacing: 10) {
                        Text(model.strings.text(.launchAgentFocusSummary))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        LazyVGrid(columns: [GridItem(.adaptive(minimum: 220), spacing: 10)], spacing: 10) {
                            SurfaceCard(emphasis: 0.25) {
                                VStack(alignment: .leading, spacing: 6) {
                                    CardTitleSummary(
                                        title: model.strings.text(.currentState),
                                        summary: launchAgentSummaryText ?? model.strings.text(.none)
                                    )
                                    if let returnCode = model.daemonState?.launchagentStatus?["returncode"]?.displayText {
                                        Text("\(model.strings.text(.returnCode)): \(returnCode)")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            SurfaceCard(emphasis: 0.25) {
                                VStack(alignment: .leading, spacing: 6) {
                                    CardTitleSummary(
                                        title: model.strings.text(.reviewPreviews),
                                        summary: runtimeInitSummary
                                    )
                                    DetailLabelValueRow(
                                        label: model.strings.diagnosticSummaryLabel("cleanup_preview"),
                                        value: cleanupSummary
                                    )
                                    DetailLabelValueRow(
                                        label: model.strings.diagnosticSummaryLabel("repair_preview"),
                                        value: repairSummary
                                    )
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            if let command = launchAgentAssistCommand {
                                SurfaceCard(emphasis: 0.25) {
                                    VStack(alignment: .leading, spacing: 6) {
                                        HStack(alignment: .top, spacing: 8) {
                                            CardTitleSummary(
                                                title: model.strings.text(.nextCommand),
                                                summary: launchAgentAssistSummary
                                            )
                                            Spacer()
                                            StatusBadge(
                                                text: model.strings.commandPriorityTitle(for: command),
                                                tone: launchAgentAssistTone
                                            )
                                        }
                                        CommandRowView(
                                            command: command,
                                            font: .system(.caption, design: .monospaced),
                                            foregroundColor: .secondary,
                                            lineLimit: 2
                                        )
                                    }
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                }
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                compactDisclosureSection(
                    title: model.strings.text(.currentStateDetails),
                    isExpanded: $showLaunchAgentCurrentStateDetails
                ) {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Spacer()
                            Button(model.strings.text(.copyCurrentState)) {
                                model.copyLaunchAgentCurrentState()
                            }
                        }
                        Text(model.strings.text(.currentStateDetailsSummary))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        SelectableMonospaceText(text: model.daemonState?.launchagentSummary.plistPath ?? model.strings.text(.none))
                        if let loadedStatus = model.daemonState?.launchagentSummary.loadedStatus {
                            DetailBadgeRow(
                                label: model.strings.text(.loadedStatus),
                                badgeText: model.strings.tokenLabel(loadedStatus),
                                tone: model.strings.tone(forToken: loadedStatus)
                            )
                        } else {
                            DetailLabelValueRow(label: model.strings.text(.loadedStatus), value: model.strings.text(.none))
                        }
                    }
                }
                compactDisclosureSection(
                    title: model.strings.text(.recoveryPreviewDetails),
                    isExpanded: $showLaunchAgentRecoveryPreview
                ) {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Spacer()
                            Button(model.strings.text(.copyRecoveryPreview)) {
                                model.copyLaunchAgentRecoveryPreview()
                            }
                        }
                        Text(model.strings.text(.recoveryPreviewDetailsSummary))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        diagnosticGroup(title: model.strings.text(.needsAttention), tone: .critical, items: needsAttentionDiagnostics)
                        diagnosticGroup(title: model.strings.text(.verifyNow), tone: .caution, items: verifyNowDiagnostics)
                        diagnosticGroup(title: model.strings.text(.healthySignals), tone: .positive, items: healthyDiagnostics)
                    }
                }
                commandDeck
                compactDisclosureSection(
                    title: model.strings.text(.statusDiagnostics),
                    isExpanded: $showLaunchAgentStatusDiagnostics
                ) {
                    metadataGroup(title: model.strings.text(.statusDiagnostics), values: launchAgentStatusDiagnostics)
                }
                if let stderrPreview = launchAgentStatusStderrPreview {
                    compactDisclosureSection(
                        title: model.strings.text(.stderrPreview),
                        isExpanded: $showLaunchAgentStderrPreview
                    ) {
                        SelectableMonospaceText(
                            text: stderrPreview,
                            font: .system(.caption, design: .monospaced),
                            lineLimit: 6
                        )
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
    }

    private var commandDeck: some View {
        GroupBox(model.strings.text(.commandDeck)) {
            VStack(alignment: .leading, spacing: 12) {
                commandDeckSection(
                    title: model.strings.text(.inspectActions),
                    tone: .positive,
                    summary: model.strings.text(.inspectActionsSummary),
                    commands: inspectCommands,
                    extraButtons: {
                        HStack {
                            Button(model.strings.text(.openPlist)) {
                                model.openLaunchAgentPlist()
                            }
                            Button(model.strings.text(.openRuntime)) {
                                model.openRuntimeDirectory()
                            }
                        }
                    }
                )
                commandDeckSection(
                    title: model.strings.text(.recoverActions),
                    tone: .critical,
                    summary: model.strings.text(.recoverActionsSummary),
                    commands: recoverCommands
                )
                commandDeckSection(
                    title: model.strings.text(.startActions),
                    tone: .caution,
                    summary: model.strings.text(.startActionsSummary),
                    commands: startCommands
                )
                commandDeckSection(
                    title: model.strings.text(.logActions),
                    tone: .neutral,
                    summary: model.strings.text(.logActionsSummary),
                    commands: logCommands,
                    extraButtons: {
                        HStack {
                            Button(model.strings.text(.copyStdoutTail)) {
                                model.copyLaunchAgentLogTailCommand(kind: "stdout")
                            }
                            Button(model.strings.text(.copyStderrTail)) {
                                model.copyLaunchAgentLogTailCommand(kind: "stderr")
                            }
                        }
                    }
                )
            }
        }
    }

    private var launchAgentRunbook: some View {
        expandableSection(
            title: model.strings.text(.launchAgentRunbook),
            summary: launchAgentRunbookSummary,
            isExpanded: $showLaunchAgentRunbook
        ) {
            VStack(alignment: .leading, spacing: 10) {
                Text(model.strings.text(.proofDiagnosticsSummary))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                commandListGroup(
                    title: model.strings.text(.preflightChecks),
                    commands: preflightChecks
                )
                if let commands = model.daemonState?.launchagentSummary.launchctlCommands {
                    commandListGroup(
                        title: model.strings.text(.verification),
                        commands: verificationCommands(commands: commands)
                    )
                }
                if !proofDiagnosticCommands.isEmpty {
                    compactDisclosureSection(
                        title: model.strings.text(.proofDiagnostics),
                        isExpanded: $showRunbookProofDiagnostics
                    ) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(model.strings.text(.proofDiagnosticsSummary))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            ForEach(proofDiagnosticCommands, id: \.self) { command in
                                commandRow(command)
                            }
                        }
                    }
                }
                metadataGroup(
                    title: model.strings.text(.logPaths),
                    values: logPaths
                )
                commandListGroup(
                    title: model.strings.text(.tailLogs),
                    commands: logTailCommands
                )
                metadataGroup(
                    title: model.strings.text(.environmentAssumptions),
                    values: environmentAssumptions
                )
                metadataGroup(
                    title: model.strings.text(.programArguments),
                    values: model.daemonState?.launchagentPreview?["program_arguments"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                metadataGroup(
                    title: model.strings.text(.previewMetadata),
                    values: previewMetadata
                )
                if let plistXML = model.daemonState?.launchagentPreview?["plist_xml"]?.stringValue {
                    compactDisclosureSection(
                        title: model.strings.text(.plistPreview),
                        isExpanded: $showRunbookPlistPreview
                    ) {
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Spacer()
                                Button(model.strings.text(.copyPlist)) {
                                    model.copyLaunchAgentPlistXML()
                                }
                            }
                            SelectableMonospaceText(
                                text: plistXML,
                                font: .system(.caption, design: .monospaced),
                                lineLimit: 12
                            )
                        }
                    }
                }
                metadataGroup(
                    title: model.strings.text(.securityBoundary),
                    values: securityBoundaryNotes
                )
                metadataGroup(
                    title: model.strings.text(.previewApplyBoundary),
                    values: previewApplyBoundaryNotes
                )
                metadataGroup(
                    title: model.strings.text(.troubleshooting),
                    values: troubleshootingNotes
                )
            }
        }
    }

    @ViewBuilder
    private func commandListGroup(title: String, commands: [String]) -> some View {
        if !commands.isEmpty {
            GroupBox(title) {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(commands, id: \.self) { command in
                        commandRow(command)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    @ViewBuilder
    private func metadataGroup(title: String, values: [String]) -> some View {
        if !values.isEmpty {
            GroupBox(title) {
                VStack(alignment: .leading, spacing: 4) {
                    BulletListView(values: values)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    private func expandableSection<Content: View>(
        title: String,
        summary: String?,
        isExpanded: Binding<Bool>,
        @ViewBuilder content: @escaping () -> Content
    ) -> some View {
        GroupBox {
            DisclosureGroup(isExpanded: isExpanded) {
                VStack(alignment: .leading, spacing: 10) {
                    content()
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 8)
            } label: {
                VStack(alignment: .leading, spacing: 4) {
                    Text(title).font(.title3).bold()
                    if let summary, !summary.isEmpty {
                        Text(summary)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    private var nextActions: some View {
        GroupBox(model.strings.text(.nextActions)) {
            VStack(alignment: .leading, spacing: 10) {
                if (model.daemonState?.nextActions ?? []).isEmpty {
                    StateCardView(
                        icon: "checkmark.circle",
                        title: model.strings.text(.nextActions),
                        message: model.strings.text(.noNextActions),
                        tone: .positive,
                        badgeText: model.strings.text(.healthySignals),
                        actionTitle: model.toolbarRefreshText,
                        actionEnabled: !model.bridgeRecoveryActionDisabled,
                        action: { Task { await model.refreshCurrentScreen() } }
                    )
                } else {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 250), spacing: 10)], spacing: 10) {
                        ForEach(Array((model.daemonState?.nextActions ?? []).prefix(3))) { action in
                            SurfaceCard(emphasis: 0.24) {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack(alignment: .top, spacing: 8) {
                                        StatusBadge(text: actionPriorityTitle(action), tone: actionPriorityTone(action))
                                        Spacer()
                                    }
                                    commandRow(action.command)
                                    if !action.reason.isEmpty {
                                        Text("\(model.strings.text(.reason)): \(action.reason)")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                    }
                    if (model.daemonState?.nextActions.count ?? 0) > 3 {
                        Text(model.strings.moreItemsMessage((model.daemonState?.nextActions.count ?? 0) - 3))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func commandRow(_ command: String) -> some View {
        CommandRowView(command: command, copyLabel: model.strings.text(.copyCommand)) { copiedCommand in
            model.copyToClipboard(copiedCommand, message: model.strings.text(.copiedCommand))
        }
    }

    private func setAllExpanded(_ isExpanded: Bool) {
        showOperatorPhase = isExpanded
        showServiceLifecycle = isExpanded
        showSupervision = isExpanded
        showRecoveryPolicy = isExpanded
        showLaunchAgent = isExpanded
        showLaunchAgentRunbook = isExpanded
    }

    private func expandSection(_ anchor: SectionAnchor) {
        switch anchor {
        case .operatorWorkspace:
            break
        case .packagingModels:
            break
        case .operatorPhase:
            showOperatorPhase = true
        case .serviceLifecycle:
            showServiceLifecycle = true
        case .supervision:
            showSupervision = true
        case .recoveryPolicy:
            showRecoveryPolicy = true
        case .launchAgent:
            showLaunchAgent = true
        case .launchAgentRunbook:
            showLaunchAgentRunbook = true
        case .nextActions:
            break
        }
    }

    private var navigationItems: [(anchor: SectionAnchor, title: String, tone: StatusTone)] {
        [
            (.operatorWorkspace, model.strings.text(.nextEpicWorkspace), .caution),
            (.packagingModels, model.strings.text(.packagingModels), .neutral),
            (.operatorPhase, model.strings.text(.operatorPhase), .caution),
            (.serviceLifecycle, model.strings.text(.serviceLifecycle), .neutral),
            (.supervision, model.strings.text(.supervision), .neutral),
            (.recoveryPolicy, model.strings.text(.recoveryPolicy), .critical),
            (.launchAgent, model.strings.text(.launchAgent), .positive),
            (.launchAgentRunbook, model.strings.text(.launchAgentRunbook), .caution),
            (.nextActions, model.strings.text(.nextActions), .positive),
        ]
    }

    private var priorityNavigationItems: [(anchor: SectionAnchor, title: String, tone: StatusTone)] {
        let priorityAnchors = Array(
            NSOrderedSet(
                array:
                    daemonFocusItems.map(\.anchor)
                    + operatorSummaryRailItems.map(\.anchor)
                    + [SectionAnchor.operatorWorkspace]
            )
        ).compactMap { $0 as? SectionAnchor }

        let byAnchor = Dictionary(uniqueKeysWithValues: navigationItems.map { ($0.anchor, $0) })
        return priorityAnchors.compactMap { byAnchor[$0] }
    }

    private var secondaryNavigationItems: [(anchor: SectionAnchor, title: String, tone: StatusTone)] {
        let used = Set(priorityNavigationItems.map(\.anchor))
        return navigationItems.filter { !used.contains($0.anchor) }
    }

    private var priorityAnchors: [SectionAnchor] {
        Array(
            NSOrderedSet(
                array:
                    daemonFocusItems.map(\.anchor)
                    + operatorSummaryRailItems.map(\.anchor)
                    + [SectionAnchor.operatorWorkspace]
            )
        ).compactMap { $0 as? SectionAnchor }
    }

    private func anchorPriority(_ anchor: SectionAnchor) -> Int {
        priorityAnchors.firstIndex(of: anchor) ?? Int.max
    }

    private var orderedDeeperReviewBlocks: [DeeperReviewBlock] {
        DeeperReviewBlock.allCases.sorted { lhs, rhs in
            let lhsPriority = deeperReviewBlockPriority(lhs)
            let rhsPriority = deeperReviewBlockPriority(rhs)
            if lhsPriority != rhsPriority {
                return lhsPriority < rhsPriority
            }
            return lhs.rawValue < rhs.rawValue
        }
    }

    private func deeperReviewBlockPriority(_ block: DeeperReviewBlock) -> Int {
        switch block {
        case .phaseClosureGates:
            return orderedPhaseClosureGateItems.map(\.anchor).map(anchorPriority).min() ?? Int.max
        case .decisionAssist:
            return orderedDecisionAssistItems.map(\.anchor).map(anchorPriority).min() ?? Int.max
        case .evidenceDrilldown:
            return orderedEvidenceEntries.map(\.anchor).map(anchorPriority).min() ?? Int.max
        case .remainingWorkstreams:
            return workspaceDisplayItems.map(\.anchor).map(anchorPriority).min() ?? Int.max
        }
    }

    private var daemonFocusItems: [FocusItem] {
        var items: [FocusItem] = []

        if let startupCommand = model.startupCommandText {
            items.append(
                FocusItem(
                    id: "supported-path",
                    title: model.strings.text(.supportedPath),
                    summary: startupCommand,
                    badge: model.strings.text(.recommended),
                    tone: .positive,
                    anchor: .operatorPhase
                )
            )
        }

        if let action = model.daemonState?.nextActions.first {
            items.append(
                FocusItem(
                    id: "next-action",
                    title: model.strings.text(.reviewDaemonAction),
                    summary: action.reason.isEmpty ? action.command : action.reason,
                    badge: actionPriorityTitle(action),
                    tone: actionPriorityTone(action),
                    anchor: focusAnchor(for: action.command)
                )
            )
        }

        if let loadedStatus = model.daemonState?.launchagentSummary.loadedStatus {
            items.append(
                FocusItem(
                    id: "launchagent-status",
                    title: model.strings.text(.checkLaunchAgentStatus),
                    summary: model.strings.tokenLabel(loadedStatus),
                    badge: model.strings.text(.launchAgent),
                    tone: model.strings.tone(forToken: loadedStatus),
                    anchor: .launchAgent
                )
            )
        }

        if !preflightChecks.isEmpty {
            items.append(
                FocusItem(
                    id: "launchagent-runbook",
                    title: model.strings.text(.openRunbook),
                    summary: model.strings.text(.launchAgentRunbook),
                    badge: model.strings.text(.verification),
                    tone: .caution,
                    anchor: .launchAgentRunbook
                )
            )
        }

        return items
    }

    private func focusAnchor(for command: String) -> SectionAnchor {
        if command.contains("preflight") || command.contains("runtime-init") || command.contains("cleanup") || command.contains("repair") {
            return .launchAgentRunbook
        }
        if command.contains("service-control-boundary") || command.contains("service-targets-status") {
            return .serviceLifecycle
        }
        if command.contains("supervision-status") {
            return .supervision
        }
        if command.contains("recovery-consent-status") {
            return .recoveryPolicy
        }
        if command.contains("packaging-status") {
            return .packagingModels
        }
        if command.contains("operator-phase-status") {
            return .operatorPhase
        }
        return .nextActions
    }

    @ViewBuilder
    private func stringList(title: String, values: [String]) -> some View {
        TitledBulletListView(title: title, values: values)
    }

    @ViewBuilder
    private func diagnosticGroup(title: String, tone: StatusTone, items: [String]) -> some View {
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    StatusBadge(text: title, tone: tone)
                    Spacer()
                }
                BulletListView(values: items)
            }
        }
    }

    @ViewBuilder
    private func commandDeckSection<ExtraButtons: View>(
        title: String,
        tone: StatusTone,
        summary: String,
        commands: [String],
        @ViewBuilder extraButtons: () -> ExtraButtons = { EmptyView() }
    ) -> some View {
        if !commands.isEmpty || !(ExtraButtons.self == EmptyView.self) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    StatusBadge(text: title, tone: tone)
                    Spacer()
                }
                Text(summary)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                ForEach(commands, id: \.self) { command in
                    commandRow(command)
                }
                extraButtons()
            }
        }
    }

    private var runtimeInitSummary: String {
        guard let payload = model.daemonState?.runtimeInit else {
            return model.strings.text(.none)
        }
        let reviewRequired = payload["review_required"]?.boolValue == true
        let itemCount = payload["items"]?.arrayValue?.count ?? 0
        return model.strings.runtimeInitSummary(reviewRequired: reviewRequired, itemCount: itemCount)
    }

    private var cleanupSummary: String {
        guard
            let decisions = model.daemonState?.cleanupPreview["decision_report"]?.objectValue?["decisions"]?.arrayValue
        else {
            return model.strings.text(.none)
        }
        return model.strings.cleanupSummary(removeCount: cleanupRemovableCount, totalCount: decisions.count)
    }

    private var repairSummary: String {
        guard let decisions = model.daemonState?.repairPreview["decisions"]?.objectValue else {
            return model.strings.text(.none)
        }
        return model.strings.repairSummary(missingCount: repairMissingCount, totalCount: decisions.count)
    }

    private var preflightChecks: [String] {
        [
            "sayane init",
            "sayane serve --host 127.0.0.1 --port 38741",
            "curl -s http://127.0.0.1:38741/health",
            "sayane app daemon-preflight --json",
            "sayane app daemon-preflight --json --include-event-record",
            "which sayane",
        ]
    }

    private func verificationCommands(commands: [String: String]) -> [String] {
        var values: [String] = []
        if let bootstrap = commands["bootstrap"] {
            values.append(bootstrap)
        }
        if let kickstart = commands["kickstart"] {
            values.append(kickstart)
        }
        if let bootout = commands["bootout"] {
            values.append(bootout)
        }
        if let printCommand = model.daemonState?.launchagentStatus?["print_command"]?.stringValue {
            values.append(printCommand)
        }
        values.append("curl -s http://127.0.0.1:38741/health")
        return values
    }

    private var logPaths: [String] {
        let preview = model.daemonState?.launchagentPreview
        var values: [String] = []
        if let stdout = preview?["stdout_path"]?.stringValue {
            values.append(stdout)
        }
        if let stderr = preview?["stderr_path"]?.stringValue {
            values.append(stderr)
        }
        return values.isEmpty ? [model.strings.text(.none)] : values
    }

    private var logTailCommands: [String] {
        let preview = model.daemonState?.launchagentPreview
        var values: [String] = []
        if let stdout = preview?["stdout_path"]?.stringValue {
            values.append("tail -f \(stdout)")
        }
        if let stderr = preview?["stderr_path"]?.stringValue {
            values.append("tail -f \(stderr)")
        }
        return values.isEmpty ? [model.strings.text(.none)] : values
    }

    private var proofDiagnosticCommands: [String] {
        [
            "sayane app daemon-identity-proof --json",
            "sayane app daemon-readiness-proof --operation-class bridge_health --json",
            "sayane app daemon-api-readiness-proof --operation-class bridge_health --json",
            "sayane app daemon-proof-diagnostics --operation-class bridge_health --json",
        ]
    }

    private var securityBoundaryNotes: [String] {
        model.strings.securityBoundaryNotes()
    }

    private var previewApplyBoundaryNotes: [String] {
        model.strings.previewApplyBoundaryNotes()
    }

    private var environmentAssumptions: [String] {
        var values: [String] = []
        if let plistPath = model.daemonState?.launchagentSummary.plistPath {
            values.append(model.strings.environmentAssumptionLabel("plist_path", value: plistPath))
        }
        if let runtimeRoot = model.daemonState?.runtimeInit["runtime_root"]?.stringValue {
            values.append(model.strings.environmentAssumptionLabel("runtime_root", value: runtimeRoot))
        }
        values.append(model.strings.environmentAssumptionLabel("service_manager", value: "launchd"))
        values.append(model.strings.environmentAssumptionLabel("working_model", value: "local Python CLI + Local Bridge"))
        return values
    }

    private var previewMetadata: [String] {
        var values: [String] = []
        if let operationID = model.daemonState?.launchagentPreview?["operation_id"]?.stringValue {
            values.append("\(model.strings.text(.operationId)): \(operationID)")
        }
        if let previewHash = model.daemonState?.launchagentPreview?["preview_hash"]?.stringValue {
            values.append("\(model.strings.text(.previewHash)): \(previewHash)")
        }
        if let label = model.daemonState?.launchagentPreview?["label"]?.stringValue {
            values.append("\(model.strings.fieldLabel("label")): \(label)")
        }
        return values
    }

    private var launchAgentStatusDiagnostics: [String] {
        var values: [String] = []
        if let loaded = model.daemonState?.launchagentStatus?["loaded"]?.boolValue {
            values.append("\(model.strings.fieldLabel("loaded")): \(model.strings.booleanValueLabel(loaded))")
        }
        if let returnCode = model.daemonState?.launchagentStatus?["returncode"]?.displayText {
            values.append("\(model.strings.text(.returnCode)): \(returnCode)")
        }
        if let plistExists = model.daemonState?.launchagentStatus?["plist_exists"]?.boolValue {
            values.append("\(model.strings.fieldLabel("plist_exists")): \(model.strings.booleanValueLabel(plistExists))")
        }
        return values
    }

    private var inspectCommands: [String] {
        var values: [String] = []
        if let printCommand = model.daemonState?.launchagentStatus?["print_command"]?.stringValue {
            values.append(printCommand)
        }
        values.append("curl -s http://127.0.0.1:38741/health")
        return Array(NSOrderedSet(array: values)) as? [String] ?? values
    }

    private var startCommands: [String] {
        let commands = model.daemonState?.launchagentSummary.launchctlCommands ?? [:]
        return ["bootstrap", "kickstart"].compactMap { commands[$0] }
    }

    private var recoverCommands: [String] {
        var values: [String] = []
        let commands = model.daemonState?.launchagentSummary.launchctlCommands ?? [:]
        values.append(contentsOf: model.daemonState?.nextActions.map(\.command).filter {
            $0.contains("repair") || $0.contains("cleanup") || $0.contains("bootout")
        } ?? [])
        if let bootout = commands["bootout"] {
            values.append(bootout)
        }
        values.sort { lhs, rhs in
            recoverCommandPriority(lhs) < recoverCommandPriority(rhs)
        }
        return Array(NSOrderedSet(array: values)) as? [String] ?? values
    }

    private var logCommands: [String] {
        logPaths + logTailCommands
    }

    private func recoverCommandPriority(_ command: String) -> Int {
        if command.contains("cleanup") {
            return 0
        }
        if command.contains("repair") {
            return 1
        }
        if command.contains("bootout") {
            return 2
        }
        return 3
    }

    private var needsAttentionDiagnostics: [String] {
        var values: [String] = []
        if model.daemonState?.runtimeInit["review_required"]?.boolValue == true {
            values.append(model.strings.diagnosticMessage("runtime_review_required"))
        }
        if cleanupRemovableCount > 0 {
            values.append(model.strings.diagnosticMessage("cleanup_remove_candidates", count: cleanupRemovableCount))
        }
        if repairMissingCount > 0 {
            values.append(model.strings.diagnosticMessage("repair_missing_items", count: repairMissingCount))
        }
        if let stderr = launchAgentStatusStderrPreview, !stderr.isEmpty {
            values.append(model.strings.diagnosticMessage("stderr_attention"))
        }
        return values
    }

    private var verifyNowDiagnostics: [String] {
        var values: [String] = [
            "\(model.strings.diagnosticSummaryLabel("runtime_init")): \(runtimeInitSummary)",
            "\(model.strings.diagnosticSummaryLabel("cleanup_preview")): \(cleanupSummary)",
            "\(model.strings.diagnosticSummaryLabel("repair_preview")): \(repairSummary)",
        ]
        if let returnCode = model.daemonState?.launchagentStatus?["returncode"]?.displayText {
            values.append("\(model.strings.text(.returnCode)): \(returnCode)")
        }
        if let printCommand = model.daemonState?.launchagentStatus?["print_command"]?.stringValue {
            values.append(model.strings.diagnosticMessage("launchctl_print_available"))
            values.append(printCommand)
        }
        return values
    }

    private var healthyDiagnostics: [String] {
        var values: [String] = []
        if model.daemonState?.launchagentStatus?["loaded"]?.boolValue == true {
            values.append(model.strings.diagnosticMessage("launchagent_loaded"))
        }
        if model.daemonState?.launchagentStatus?["plist_exists"]?.boolValue == true {
            values.append(model.strings.diagnosticMessage("plist_exists"))
        }
        if cleanupRemovableCount == 0 {
            values.append(model.strings.diagnosticMessage("cleanup_clear"))
        }
        if repairMissingCount == 0 {
            values.append(model.strings.diagnosticMessage("repair_clear"))
        }
        return values
    }

    private var cleanupRemovableCount: Int {
        guard
            let decisions = model.daemonState?.cleanupPreview["decision_report"]?.objectValue?["decisions"]?.arrayValue
        else {
            return 0
        }
        return decisions.filter {
            $0.objectValue?["recommended_action"]?.stringValue == "remove"
        }.count
    }

    private var cleanupDecisionCount: Int {
        guard
            let decisions = model.daemonState?.cleanupPreview["decision_report"]?.objectValue?["decisions"]?.arrayValue
        else {
            return 0
        }
        return decisions.count
    }

    private var repairMissingCount: Int {
        guard let decisions = model.daemonState?.repairPreview["decisions"]?.objectValue else {
            return 0
        }
        return decisions.values.filter {
            $0.objectValue?["status"]?.stringValue == "missing"
        }.count
    }

    private var launchAgentStatusStderrPreview: String? {
        guard let stderr = model.daemonState?.launchagentStatus?["stderr"]?.stringValue,
              !stderr.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return nil
        }
        return stderr
    }

    private var operatorPhaseSectionSummary: String? {
        guard let summary = model.daemonState?.operatorPhaseSummary else { return nil }
        return [summary.phaseStatus.map(model.strings.tokenLabel), summary.phaseReadiness.map(model.strings.tokenLabel)].compactMap { $0 }.joined(separator: " · ")
    }

    private var serviceLifecycleSummary: String? {
        if let count = model.daemonState?.serviceControlBoundary?["service_plane"]?.objectValue?["lifecycle_operations"]?.arrayValue?.count {
            return "\(model.strings.text(.serviceLifecycle)): \(count)"
        }
        return nil
    }

    private var operatorWorkspaceItems: [OperatorWorkspaceItem] {
        [
            packagingWorkspaceItem,
            serviceWorkspaceItem,
            supervisionWorkspaceItem,
            recoveryWorkspaceItem,
        ].compactMap { $0 }
    }

    private var workspaceDisplayItems: [OperatorWorkspaceItem] {
        let coveredAnchors = Set(operatorSummaryRailItems.map(\.anchor))
        return operatorWorkspaceItems
            .filter { !coveredAnchors.contains($0.anchor) }
            .sorted { lhs, rhs in
                let lhsPriority = anchorPriority(lhs.anchor)
                let rhsPriority = anchorPriority(rhs.anchor)
                if lhsPriority != rhsPriority {
                    return lhsPriority < rhsPriority
                }
                return lhs.title < rhs.title
            }
    }

    private var packagingWorkspaceItem: OperatorWorkspaceItem? {
        guard let packaging = model.daemonState?.packagingStatus else { return nil }
        let currentModel = packaging["packaging_model"]?.stringValue ?? model.strings.text(.none)
        let workstream = operatorWorkstream(named: "packaging_model_decision")
        let blockedBy = packaging["packaging_decision"]?.objectValue?["candidate_models"]?.arrayValue?
            .compactMap { candidate -> String? in
                guard let object = candidate.objectValue else { return nil }
                return object["blocked_by"]?.arrayValue?.compactMap(\.stringValue).first
            }
            .first
        return OperatorWorkspaceItem(
            id: "packaging",
            anchor: .packagingModels,
            phaseItem: "packaging_model_decision",
            title: model.strings.summaryCardLabel("packaging_model_decision"),
            status: model.strings.tokenLabel(workstream?.status ?? currentModel),
            tone: model.strings.tone(forToken: workstream?.status ?? currentModel),
            summary: model.strings.tokenLabel(currentModel),
            detail: blockedBy ?? workstream?.detail,
            command: "sayane app daemon-packaging-status --json",
            blockers: packagingBlockers
        )
    }

    private var serviceWorkspaceItem: OperatorWorkspaceItem? {
        guard let serviceTargets = model.daemonState?.serviceTargetsStatus else { return nil }
        let currentPlatform = serviceTargets["current_platform"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let recommendedTarget = serviceTargets["recommended_target"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let gate = serviceTargets["policy_gates"]?.objectValue?["hybrid_packaging_gate"]?.stringValue
        let workstream = operatorWorkstream(named: "service_integration_line")
        return OperatorWorkspaceItem(
            id: "service",
            anchor: .serviceLifecycle,
            phaseItem: "service_control_boundary_definition",
            title: model.strings.summaryCardLabel("service_integration_line"),
            status: model.strings.tokenLabel(workstream?.status ?? "in_progress"),
            tone: model.strings.tone(forToken: workstream?.status ?? "in_progress"),
            summary: "\(currentPlatform) → \(recommendedTarget)",
            detail: gate.map(model.strings.tokenLabel) ?? workstream?.detail,
            command: "sayane app daemon-service-targets-status --json",
            blockers: serviceBlockers
        )
    }

    private var supervisionWorkspaceItem: OperatorWorkspaceItem? {
        guard let supervision = model.daemonState?.supervisionStatus else { return nil }
        let mode = supervision["supervision_mode"]?.stringValue ?? model.strings.text(.none)
        let candidateSurface = supervision["background_surfaces"]?.objectValue?["candidate_surfaces"]?.arrayValue?
            .compactMap { $0.objectValue?["surface"]?.stringValue }
            .first
        let workstream = operatorWorkstream(named: "supervision_ux_line")
        return OperatorWorkspaceItem(
            id: "supervision",
            anchor: .supervision,
            phaseItem: "supervision_ux_decision",
            title: model.strings.summaryCardLabel("supervision_ux_line"),
            status: model.strings.tokenLabel(workstream?.status ?? mode),
            tone: model.strings.tone(forToken: workstream?.status ?? mode),
            summary: model.strings.tokenLabel(mode),
            detail: candidateSurface.map(model.strings.tokenLabel) ?? workstream?.detail,
            command: "sayane app daemon-supervision-status --json",
            blockers: supervisionBlockers
        )
    }

    private var recoveryWorkspaceItem: OperatorWorkspaceItem? {
        guard let recovery = model.daemonState?.recoveryConsentStatus else { return nil }
        let consent = recovery["consent_model"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let recoveryModel = recovery["recovery_model"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let flow = recovery["recommended_recovery_flow"]?.arrayValue?.compactMap(\.stringValue).first
        let workstream = operatorWorkstream(named: "recovery_and_consent_line")
        return OperatorWorkspaceItem(
            id: "recovery",
            anchor: .recoveryPolicy,
            phaseItem: "consent_and_recovery_alignment",
            title: model.strings.summaryCardLabel("recovery_and_consent_line"),
            status: model.strings.tokenLabel(workstream?.status ?? recovery["phase_status"]?.stringValue ?? "baseline_ready"),
            tone: model.strings.tone(forToken: workstream?.status ?? recovery["phase_status"]?.stringValue ?? "baseline_ready"),
            summary: "\(consent) · \(recoveryModel)",
            detail: flow ?? workstream?.detail,
            command: "sayane app daemon-recovery-consent-status --json",
            blockers: recoveryBlockers
        )
    }

    private func operatorWorkstream(named name: String) -> Workstream? {
        model.daemonState?.operatorPhaseDetails.workstreams.first { $0.name == name }
    }

    private var implementationOrderItems: [String] {
        model.daemonState?.operatorPhaseDetails.recommendedImplementationOrder ?? []
    }

    private var phaseClosureGateItems: [PhaseClosureGateItem] {
        (phaseChecklistItems ?? []).compactMap { item in
            guard let destination = phaseClosureDestination(for: item.name) else { return nil }
            return PhaseClosureGateItem(
                id: item.name,
                title: model.strings.summaryCardLabel(item.name),
                status: model.strings.tokenLabel(item.status),
                blockers: item.blockingReasons,
                command: destination.command,
                anchor: destination.anchor,
                tone: model.strings.tone(forToken: item.status)
            )
        }
    }

    private var orderedPhaseClosureGateItems: [PhaseClosureGateItem] {
        phaseClosureGateItems.sorted { lhs, rhs in
            let lhsPriority = anchorPriority(lhs.anchor)
            let rhsPriority = anchorPriority(rhs.anchor)
            if lhsPriority != rhsPriority {
                return lhsPriority < rhsPriority
            }
            return lhs.title < rhs.title
        }
    }

    private func phaseClosureDestination(for itemName: String) -> (anchor: SectionAnchor, command: String)? {
        switch itemName {
        case "supported_packaging_model_finalized":
            (.packagingModels, "sayane app daemon-packaging-status --json")
        case "service_lifecycle_implementation_closed":
            (.serviceLifecycle, "sayane app daemon-service-control-boundary --json")
        case "platform_policy_and_rollback_closed":
            (.serviceLifecycle, "sayane app daemon-service-targets-status --json")
        case "background_supervision_direction_decided":
            (.supervision, "sayane app daemon-supervision-status --json")
        case "recovery_and_consent_path_remains_explicit_under_next_model":
            (.recoveryPolicy, "sayane app daemon-recovery-consent-status --json")
        default:
            nil
        }
    }

    private var decisionAssistItems: [DecisionAssistItem] {
        var items: [DecisionAssistItem] = []
        if let command = serviceAssistCommand {
            items.append(
                DecisionAssistItem(
                    id: "service-assist",
                    title: model.strings.text(.serviceLifecycle),
                    summary: serviceAssistSummary,
                    command: command,
                    anchor: .serviceLifecycle,
                    tone: .caution
                )
            )
        }
        if let command = recoveryAssistCommand {
            items.append(
                DecisionAssistItem(
                    id: "recovery-assist",
                    title: model.strings.text(.recoveryPolicy),
                    summary: recoveryAssistSummary,
                    command: command,
                    anchor: .recoveryPolicy,
                    tone: .critical
                )
            )
        }
        if let command = supervisionAssistCommand {
            items.append(
                DecisionAssistItem(
                    id: "supervision-assist",
                    title: model.strings.text(.supervision),
                    summary: supervisionAssistSummary,
                    command: command,
                    anchor: .supervision,
                    tone: .neutral
                )
            )
        }
        if let command = launchAgentAssistCommand {
            items.append(
                DecisionAssistItem(
                    id: "launchagent-assist",
                    title: model.strings.text(.launchAgent),
                    summary: launchAgentAssistSummary,
                    command: command,
                    anchor: .launchAgentRunbook,
                    tone: launchAgentAssistTone
                )
            )
        }
        return items
    }

    private var orderedDecisionAssistItems: [DecisionAssistItem] {
        decisionAssistItems.sorted { lhs, rhs in
            let lhsPriority = anchorPriority(lhs.anchor)
            let rhsPriority = anchorPriority(rhs.anchor)
            if lhsPriority != rhsPriority {
                return lhsPriority < rhsPriority
            }
            return lhs.title < rhs.title
        }
    }

    private var evidenceEntries: [EvidenceEntry] {
        [
            EvidenceEntry(
                id: "operator-phase",
                title: model.strings.text(.operatorPhase),
                command: "sayane app daemon-operator-phase-status --json",
                anchor: .operatorPhase,
                tone: .caution,
                snapshot: operatorPhaseSnapshot,
                detail: operatorPhaseDetail
            ),
            EvidenceEntry(
                id: "packaging",
                title: model.strings.text(.packagingModels),
                command: "sayane app daemon-packaging-status --json",
                anchor: .packagingModels,
                tone: .neutral,
                snapshot: packagingEvidenceSnapshot,
                detail: packagingEvidenceDetail
            ),
            EvidenceEntry(
                id: "service-targets",
                title: model.strings.text(.serviceTargets),
                command: "sayane app daemon-service-targets-status --json",
                anchor: .serviceLifecycle,
                tone: .neutral,
                snapshot: serviceTargetsEvidenceSnapshot,
                detail: serviceTargetsEvidenceDetail
            ),
            EvidenceEntry(
                id: "service-boundary",
                title: model.strings.summaryCardLabel("service_control_boundary_definition"),
                command: "sayane app daemon-service-control-boundary --json",
                anchor: .serviceLifecycle,
                tone: .critical,
                snapshot: serviceBoundaryEvidenceSnapshot,
                detail: serviceBoundaryEvidenceDetail
            ),
            EvidenceEntry(
                id: "supervision",
                title: model.strings.text(.supervision),
                command: "sayane app daemon-supervision-status --json",
                anchor: .supervision,
                tone: .neutral,
                snapshot: supervisionEvidenceSnapshot,
                detail: supervisionEvidenceDetail
            ),
            EvidenceEntry(
                id: "recovery",
                title: model.strings.text(.recoveryPolicy),
                command: "sayane app daemon-recovery-consent-status --json",
                anchor: .recoveryPolicy,
                tone: .caution,
                snapshot: recoveryEvidenceSnapshot,
                detail: recoveryEvidenceDetail
            ),
        ]
    }

    private var orderedEvidenceEntries: [EvidenceEntry] {
        evidenceEntries.sorted { lhs, rhs in
            let lhsPriority = anchorPriority(lhs.anchor)
            let rhsPriority = anchorPriority(rhs.anchor)
            if lhsPriority != rhsPriority {
                return lhsPriority < rhsPriority
            }
            return lhs.title < rhs.title
        }
    }

    private var operatorPhaseSnapshot: String {
        let readiness = model.daemonState?.operatorPhaseSummary.phaseReadiness.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let status = model.daemonState?.operatorPhaseSummary.phaseStatus.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        return "\(readiness) · \(status)"
    }

    private var operatorPhaseDetail: String? {
        model.daemonState?.operatorPhaseSummary.blockingReasons.first.map(model.strings.tokenLabel)
    }

    private var serviceAssistCommand: String? {
        if let command = model.daemonState?.serviceControlBoundary?["control_plane"]?.objectValue?["allowed_commands"]?.arrayValue?
            .compactMap({ $0.objectValue?["command"]?.stringValue }).first {
            return command
        }
        return "sayane app daemon-service-control-boundary --json"
    }

    private var serviceAssistSummary: String {
        if let blocker = serviceBlockers.first {
            return "\(model.strings.text(.blockedBy)): \(model.strings.tokenLabel(blocker))"
        }
        return model.strings.text(.serviceControlAssistSummary)
    }

    private var recoveryAssistCommand: String? {
        if let command = model.daemonState?.recoveryConsentStatus?["control_recovery_actions"]?.arrayValue?
            .compactMap({ $0.objectValue?["command"]?.stringValue }).first {
            return command
        }
        return "sayane app daemon-recovery-consent-status --json"
    }

    private var recoveryAssistSummary: String {
        if let detail = recoveryEvidenceDetail {
            return detail
        }
        return model.strings.text(.recoveryAssistSummary)
    }

    private var supervisionAssistCommand: String? {
        "sayane app daemon-supervision-status --json"
    }

    private var supervisionAssistSummary: String {
        if let detail = supervisionEvidenceDetail {
            return detail
        }
        return model.strings.text(.supervisionAssistSummary)
    }

    private var launchAgentAssistCommand: String? {
        if model.daemonState?.runtimeInit["review_required"]?.boolValue == true {
            return "sayane app daemon-runtime-init --json"
        }
        if cleanupRemovableCount > 0 {
            return "sayane app daemon-cleanup-preview --json"
        }
        if repairMissingCount > 0 {
            return "sayane app daemon-repair-preview --json"
        }
        if let printCommand = model.daemonState?.launchagentStatus?["print_command"]?.stringValue,
           !printCommand.isEmpty {
            return printCommand
        }
        return model.daemonState?.launchagentSummary.launchctlCommands?["bootstrap"]
    }

    private var launchAgentAssistSummary: String {
        if model.daemonState?.runtimeInit["review_required"]?.boolValue == true {
            return model.strings.text(.launchAgentAssistRuntimeInit)
        }
        if cleanupRemovableCount > 0 {
            return model.strings.cleanupSummary(removeCount: cleanupRemovableCount, totalCount: cleanupDecisionCount)
        }
        if repairMissingCount > 0 {
            return model.strings.diagnosticMessage("repair_missing_items", count: repairMissingCount)
        }
        if let returnCode = model.daemonState?.launchagentStatus?["returncode"]?.displayText {
            return "\(model.strings.text(.returnCode)): \(returnCode)"
        }
        return model.strings.text(.launchAgentAssistHealthy)
    }

    private var launchAgentAssistTone: StatusTone {
        if model.daemonState?.runtimeInit["review_required"]?.boolValue == true || cleanupRemovableCount > 0 || repairMissingCount > 0 {
            return .critical
        }
        if model.daemonState?.launchagentStatus?["loaded"]?.boolValue == true {
            return .positive
        }
        return .caution
    }

    private var packagingEvidenceSnapshot: String {
        let current = model.daemonState?.packagingStatus?["packaging_model"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let candidateCount = model.daemonState?.packagingStatus?["packaging_decision"]?.objectValue?["candidate_models"]?.arrayValue?.count ?? 0
        return "\(current) · \(candidateCount)"
    }

    private var packagingEvidenceDetail: String? {
        packagingBlockers.first.map(model.strings.tokenLabel)
    }

    private var serviceTargetsEvidenceSnapshot: String {
        let platform = model.daemonState?.serviceTargetSummary.currentPlatform.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let recommended = model.daemonState?.serviceTargetSummary.recommendedTarget.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        return "\(platform) → \(recommended)"
    }

    private var serviceTargetsEvidenceDetail: String? {
        model.daemonState?.serviceTargetsStatus?["policy_gates"]?.objectValue?["hybrid_packaging_gate"]?.stringValue.map(model.strings.tokenLabel)
    }

    private var serviceBoundaryEvidenceSnapshot: String {
        let allowedCount = model.daemonState?.serviceControlBoundary?["control_plane"]?.objectValue?["allowed_commands"]?.arrayValue?.count ?? 0
        let deferredCount = model.daemonState?.serviceControlBoundary?["service_plane"]?.objectValue?["deferred_commands"]?.arrayValue?.count ?? 0
        return "\(model.strings.text(.allowedCommands)) \(allowedCount) · \(model.strings.text(.deferredCommands)) \(deferredCount)"
    }

    private var serviceBoundaryEvidenceDetail: String? {
        serviceBlockers.first.map(model.strings.tokenLabel)
    }

    private var supervisionEvidenceSnapshot: String {
        let mode = model.daemonState?.supervisionStatus?["supervision_mode"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let candidates = model.daemonState?.supervisionStatus?["background_surfaces"]?.objectValue?["candidate_surfaces"]?.arrayValue?.count ?? 0
        return "\(mode) · \(candidates)"
    }

    private var supervisionEvidenceDetail: String? {
        supervisionBlockers.first.map(model.strings.tokenLabel)
    }

    private var recoveryEvidenceSnapshot: String {
        let consent = model.daemonState?.recoveryConsentStatus?["consent_model"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        let recovery = model.daemonState?.recoveryConsentStatus?["recovery_model"]?.stringValue.map(model.strings.tokenLabel) ?? model.strings.text(.none)
        return "\(consent) · \(recovery)"
    }

    private var recoveryEvidenceDetail: String? {
        recoveryBlockers.first.map(model.strings.tokenLabel)
    }

    private func recommendedOrderIndex(for item: String) -> Int? {
        implementationOrderItems.firstIndex(of: item).map { $0 + 1 }
    }

    private struct PhaseChecklistItem {
        let name: String
        let status: String
        let blockingReasons: [String]
    }

    private var phaseChecklistItems: [PhaseChecklistItem]? {
        model.daemonState?.operatorPhaseStatus?["phase_closure_checklist"]?.arrayValue?.compactMap { value in
            guard let object = value.objectValue else { return nil }
            return PhaseChecklistItem(
                name: object["item"]?.stringValue ?? model.strings.text(.none),
                status: object["status"]?.stringValue ?? "in_progress",
                blockingReasons: object["blocking_reasons"]?.arrayValue?.compactMap(\.stringValue) ?? []
            )
        }
    }

    private var packagingBlockers: [String] {
        let candidateBlockers =
            model.daemonState?.packagingStatus?["packaging_decision"]?.objectValue?["candidate_models"]?.arrayValue?
                .flatMap { $0.objectValue?["blocked_by"]?.arrayValue?.compactMap(\.stringValue) ?? [] } ?? []
        return Array(NSOrderedSet(array: candidateBlockers)) as? [String] ?? candidateBlockers
    }

    private var serviceBlockers: [String] {
        var values = model.daemonState?.serviceControlBoundary?["service_plane"]?.objectValue?["deferred_commands"]?.arrayValue?.compactMap(\.stringValue) ?? []
        if let gate = model.daemonState?.serviceTargetsStatus?["policy_gates"]?.objectValue?["hybrid_packaging_gate"]?.stringValue {
            values.append(gate)
        }
        return values
    }

    private var supervisionBlockers: [String] {
        model.daemonState?.supervisionStatus?["background_surfaces"]?.objectValue?["candidate_surfaces"]?.arrayValue?
            .compactMap { $0.objectValue?["surface"]?.stringValue } ?? []
    }

    private var recoveryBlockers: [String] {
        model.daemonState?.recoveryConsentStatus?["app_ui_guardrails"]?.arrayValue?.compactMap(\.stringValue) ?? []
    }

    private var supervisionSummary: String? {
        model.daemonState?.supervisionStatus?["supervision_mode"]?.stringValue.map(model.strings.tokenLabel)
    }

    private var recoveryPolicySummary: String? {
        model.daemonState?.recoveryConsentStatus?["recovery_model"]?.stringValue.map(model.strings.tokenLabel)
    }

    private var launchAgentSummaryText: String? {
        let loadedStatus = model.daemonState?.launchagentSummary.loadedStatus.map(model.strings.tokenLabel)
        let returnCode = model.daemonState?.launchagentStatus?["returncode"]?.displayText
        return [loadedStatus, returnCode.map { "\(model.strings.text(.returnCode))=\($0)" }].compactMap { $0 }.joined(separator: " · ")
    }

    private var launchAgentRunbookSummary: String? {
        let op = model.daemonState?.launchagentPreview?["operation_id"]?.stringValue
        let hash = model.daemonState?.launchagentPreview?["preview_hash"]?.stringValue
        return [op, hash].compactMap { $0 }.joined(separator: " · ")
    }

    private var operatorSummaryRailItems: [OperatorSummaryRailItem] {
        var items: [OperatorSummaryRailItem] = []

        if let startupCommand = model.startupCommandText {
            items.append(
                OperatorSummaryRailItem(
                    id: "supported-path",
                    title: model.strings.text(.supportedPath),
                    summary: model.daemonState?.operatorPhaseDetails.currentSupportedOperatorPath.notes.first ?? model.strings.text(.recommended),
                    badge: model.strings.text(.startupCommand),
                    command: startupCommand,
                    anchor: .operatorPhase,
                    tone: .positive
                )
            )
        }

        if let gate = phaseClosureGateItems.first {
            let summary = gate.blockers.first.map { blocker in
                "\(model.strings.tokenLabel(gate.status)) · \(model.strings.tokenLabel(blocker))"
            } ?? model.strings.tokenLabel(gate.status)
            items.append(
                OperatorSummaryRailItem(
                    id: "current-gate",
                    title: model.strings.text(.currentGate),
                    summary: "\(gate.title) — \(summary)",
                    badge: model.strings.text(.phaseClosureGates),
                    command: gate.command,
                    anchor: gate.anchor,
                    tone: gate.tone
                )
            )
        }

        if let action = decisionAssistItems.first {
            items.append(
                OperatorSummaryRailItem(
                    id: "next-command",
                    title: model.strings.text(.nextCommand),
                    summary: action.summary,
                    badge: model.strings.text(.suggestedAction),
                    command: action.command,
                    anchor: action.anchor,
                    tone: action.tone
                )
            )
        }

        let preferredEvidence = phaseClosureGateItems.first.flatMap { gate in
            evidenceEntries.first { $0.anchor == gate.anchor }
        } ?? evidenceEntries.first
        if let evidence = preferredEvidence {
            items.append(
                OperatorSummaryRailItem(
                    id: "next-read-surface",
                    title: model.strings.text(.nextReadSurface),
                    summary: "\(evidence.title) — \(evidence.snapshot)",
                    badge: model.strings.text(.readSurfaces),
                    command: evidence.command,
                    anchor: evidence.anchor,
                    tone: evidence.tone
                )
            )
        }

        return items
    }

    private var operatorSummaryRailPreviewItems: [OperatorSummaryRailItem] {
        Array(operatorSummaryRailItems.prefix(3))
    }

    private var operatorSummaryRailOverflowCount: Int {
        max(operatorSummaryRailItems.count - operatorSummaryRailPreviewItems.count, 0)
    }

    private var decisionAssistPreviewItems: [DecisionAssistItem] {
        Array(orderedDecisionAssistItems.prefix(2))
    }

    private var decisionAssistOverflowCount: Int {
        max(orderedDecisionAssistItems.count - decisionAssistPreviewItems.count, 0)
    }

    private var evidencePreviewItems: [EvidenceEntry] {
        Array(orderedEvidenceEntries.prefix(2))
    }

    private var evidenceOverflowCount: Int {
        max(orderedEvidenceEntries.count - evidencePreviewItems.count, 0)
    }

    private var workspaceDisplayPreviewItems: [OperatorWorkspaceItem] {
        Array(workspaceDisplayItems.prefix(4))
    }

    private var workspaceDisplayOverflowCount: Int {
        max(workspaceDisplayItems.count - workspaceDisplayPreviewItems.count, 0)
    }

    private var troubleshootingNotes: [String] {
        model.strings.troubleshootingNotes()
    }

    private func actionPriorityTone(_ action: DaemonNextAction) -> StatusTone {
        model.strings.tone(forCommand: action.command)
    }

    private func actionPriorityTitle(_ action: DaemonNextAction) -> String {
        model.strings.commandPriorityTitle(for: action.command)
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
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 8)
            } label: {
                Text(title)
                    .font(.headline)
            }
        }
    }

}
