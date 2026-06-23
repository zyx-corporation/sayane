import SwiftUI

struct DaemonView: View {
    private enum SectionAnchor: String, CaseIterable {
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
    @State private var showOperatorPhase = true
    @State private var showServiceLifecycle = false
    @State private var showSupervision = false
    @State private var showRecoveryPolicy = false
    @State private var showLaunchAgent = true
    @State private var showLaunchAgentRunbook = false

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    focusSection
                    cards
                    sectionNavigator(proxy: proxy)
                    packagingModels
                        .id(SectionAnchor.packagingModels)
                    operatorPanels
                    operatorPhase
                        .id(SectionAnchor.operatorPhase)
                    handoffSnapshot
                    startupVisibility
                    serviceTargets
                    serviceLifecycle
                        .id(SectionAnchor.serviceLifecycle)
                    supervision
                        .id(SectionAnchor.supervision)
                    recoveryPolicy
                        .id(SectionAnchor.recoveryPolicy)
                    launchAgent
                        .id(SectionAnchor.launchAgent)
                    launchAgentRunbook
                        .id(SectionAnchor.launchAgentRunbook)
                    recoveryPreviews
                    nextActions
                        .id(SectionAnchor.nextActions)
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
            }
        }
    }

    private func sectionNavigator(proxy: ScrollViewProxy) -> some View {
        GroupBox(model.strings.text(.sectionNavigator)) {
            FlowLayout(navigationItems, id: \.anchor, spacing: 8) { item in
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
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var focusSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.startHere))
            if daemonFocusItems.isEmpty {
                StateCardView(
                    icon: "scope",
                    title: model.strings.text(.startHere),
                    message: model.strings.text(.noPriorityActions),
                    tone: .neutral,
                    badgeText: model.strings.text(.healthySignals),
                    actionTitle: model.strings.text(.refresh),
                    action: { Task { await model.refreshCurrentScreen() } }
                )
            } else {
                ForEach(daemonFocusItems, id: \.title) { item in
                    Button {
                        item.action()
                    } label: {
                        SurfaceCard(emphasis: 0.34) {
                            HStack(alignment: .top, spacing: 12) {
                                StatusBadge(text: item.badge, tone: item.tone)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(item.title)
                                        .font(.headline)
                                    Text(item.summary)
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                }
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

    private var cards: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.summaryCards))
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 180))], spacing: 12) {
                ForEach(model.daemonState?.summaryCards ?? []) { card in
                    SurfaceCard {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(model.strings.summaryCardLabel(card.key)).font(.caption).foregroundStyle(.secondary)
                            daemonSummaryValueView(card)
                        }
                    }
                }
            }
        }
    }

    private var operatorPanels: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle(text: model.strings.text(.status))
            ForEach(model.daemonState?.operatorPanels ?? []) { panel in
                GroupBox(model.strings.operatorPanelLabel(panel.panel)) {
                    VStack(alignment: .leading, spacing: 6) {
                        if let status = panel.status {
                            HStack {
                                Text("\(model.strings.fieldLabel("status")):")
                                StatusBadge(text: model.strings.tokenLabel(status), tone: model.strings.tone(forToken: status))
                            }
                        }
                        if let highlights = panel.highlights {
                            FlowLayout(highlights, id: \.self, spacing: 6) { highlight in
                                StatusBadge(text: model.strings.tokenLabel(highlight), tone: model.strings.tone(forToken: highlight))
                            }
                        }
                        if let commands = panel.commands, !commands.isEmpty {
                            ForEach(commands, id: \.self) { command in
                                commandRow(command)
                            }
                        }
                        if let deferred = panel.deferredCommands, !deferred.isEmpty {
                            Text("\(model.strings.text(.deferredCommands)): \(deferred.joined(separator: ", "))")
                        }
                        if let flow = panel.recommendedFlow, !flow.isEmpty {
                            Text("\(model.strings.fieldLabel("flow")): \(flow.joined(separator: " → "))")
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
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
                        Text("\(model.strings.fieldLabel("phase")): \(summary.phase.map(model.strings.tokenLabel) ?? model.strings.text(.none))")
                        HStack {
                            Text("\(model.strings.fieldLabel("status")):")
                            if let phaseStatus = summary.phaseStatus {
                                StatusBadge(text: model.strings.tokenLabel(phaseStatus), tone: model.strings.tone(forToken: phaseStatus))
                            } else {
                                Text(model.strings.text(.none))
                            }
                        }
                        HStack {
                            Text("\(model.strings.fieldLabel("readiness")):")
                            if let readiness = summary.phaseReadiness {
                                StatusBadge(text: model.strings.tokenLabel(readiness), tone: model.strings.tone(forToken: readiness))
                            } else {
                                Text(model.strings.text(.none))
                            }
                        }
                        ForEach(summary.blockingReasons, id: \.self) { Text("• \($0)") }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            if let details = model.daemonState?.operatorPhaseDetails {
                GroupBox(model.strings.text(.supportedPath)) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(details.currentSupportedOperatorPath.startupCommandText ?? model.strings.text(.none))
                        if let bootstrapUI = details.currentSupportedOperatorPath.bootstrapUI {
                            Text(bootstrapUI).foregroundStyle(.secondary)
                        }
                        ForEach(details.workstreams) { workstream in
                            Text("• \(model.strings.summaryCardLabel(workstream.name)): \(workstream.status.map(model.strings.tokenLabel) ?? "-") · \(workstream.detail ?? "")")
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                GroupBox(model.strings.text(.exitCriteria)) {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(details.exitCriteria, id: \.self) { Text("• \($0)") }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                GroupBox(model.strings.text(.readSurfaces)) {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(details.readSurfaces, id: \.self) { surface in
                            commandRow(surface)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                GroupBox(model.strings.text(.notInScope)) {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(details.notInScope, id: \.self) { Text("• \($0)") }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
    }

    private var startupVisibility: some View {
        GroupBox(model.strings.text(.startupVisibility)) {
            VStack(alignment: .leading, spacing: 10) {
                if let startup = model.daemonState?.operatorPhaseStatus?["current_supported_operator_path"]?.objectValue {
                    if let command = startup["startup_command_text"]?.stringValue {
                        Text(model.strings.text(.startupCommand)).bold()
                        commandRow(command)
                    }
                    if let bootstrapUI = startup["bootstrap_ui"]?.stringValue {
                        Text(model.strings.text(.bootstrapUI)).bold()
                        commandRow(bootstrapUI)
                    }
                    if let localOnly = startup["local_only"]?.boolValue {
                        Text("\(model.strings.text(.localOnly)): \(model.strings.booleanValueLabel(localOnly))")
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
                                    HStack {
                                        Text("\(model.strings.text(.statusValue)):")
                                        StatusBadge(text: model.strings.tokenLabel(status), tone: model.strings.tone(forToken: status))
                                    }
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
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var handoffSnapshot: some View {
        GroupBox(model.strings.text(.handoffSnapshot)) {
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
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var serviceTargets: some View {
        GroupBox(model.strings.text(.serviceTargets)) {
            VStack(alignment: .leading, spacing: 6) {
                Text("\(model.strings.text(.currentPlatform)): \(model.daemonState?.serviceTargetSummary.currentPlatform.map(model.strings.tokenLabel) ?? model.strings.text(.none))")
                Text("\(model.strings.text(.recommended)): \(model.daemonState?.serviceTargetSummary.recommendedTarget.map(model.strings.tokenLabel) ?? model.strings.text(.none))")
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
                            ForEach(notes, id: \.self) { note in
                                Text("  - \(note)").foregroundStyle(.secondary)
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
                    GroupBox(model.strings.text(.allowedCommands)) {
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(Array(allowedCommands.enumerated()), id: \.offset) { _, value in
                                if let command = value.objectValue?["command"]?.stringValue {
                                    commandRow(command)
                                }
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                if let deferredCommands = model.daemonState?.serviceControlBoundary?["service_plane"]?.objectValue?["deferred_commands"]?.arrayValue?.compactMap(\.stringValue),
                   !deferredCommands.isEmpty {
                    GroupBox(model.strings.text(.deferredCommands)) {
                        VStack(alignment: .leading, spacing: 6) {
                            FlowLayout(deferredCommands, id: \.self, spacing: 6) { command in
                                StatusBadge(text: model.strings.tokenLabel(command), tone: .caution)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
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
                                        Text("\(model.strings.text(.rollbackRequired)): \(model.strings.booleanValueLabel(rollback))")
                                    }
                                    if let policy = object["policy_required"]?.boolValue {
                                        Text("\(model.strings.text(.policyRequired)): \(model.strings.booleanValueLabel(policy))")
                                    }
                                }
                            }
                        }
                    }
                }
                if let appPolicy = model.daemonState?.serviceControlBoundary?["app_ui_policy"]?.objectValue {
                    GroupBox(model.strings.text(.appUIPolicy)) {
                        VStack(alignment: .leading, spacing: 8) {
                            stringList(title: model.strings.text(.allowedReads), values: appPolicy["allowed_reads"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                            stringList(title: model.strings.text(.forbiddenExposure), values: appPolicy["forbidden_control_exposure"]?.arrayValue?.compactMap(\.stringValue) ?? [])
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
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
                if let current = model.daemonState?.packagingStatus?["packaging_model"]?.stringValue {
                    HStack {
                        Text("\(model.strings.text(.currentValue)):")
                        StatusBadge(text: model.strings.tokenLabel(current), tone: model.strings.tone(forToken: current))
                    }
                }
                if let candidates = model.daemonState?.packagingStatus?["packaging_decision"]?.objectValue?["candidate_models"]?.arrayValue {
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
                stringList(
                    title: model.strings.text(.guardrails),
                    values: model.daemonState?.packagingStatus?["packaging_decision"]?.objectValue?["decision_guardrails"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
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
                    HStack {
                        Text("\(model.strings.text(.mode)):")
                        StatusBadge(text: model.strings.tokenLabel(mode), tone: model.strings.tone(forToken: mode))
                    }
                }
                stringList(
                    title: model.strings.text(.passiveVisibility),
                    values: model.daemonState?.supervisionStatus?["passive_visibility"]?.objectValue?["surfaces"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                stringList(
                    title: model.strings.text(.activeSupervision),
                    values: model.daemonState?.supervisionStatus?["active_supervision"]?.objectValue?["allowed_actions"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                if let candidates = model.daemonState?.supervisionStatus?["background_surfaces"]?.objectValue?["candidate_surfaces"]?.arrayValue {
                    Text(model.strings.text(.backgroundSurfaces)).bold()
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
                                        Text("\(model.strings.text(.operatorValue)): \(operatorValue)")
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
                    HStack {
                        Text("\(model.strings.text(.consent)):")
                        StatusBadge(text: model.strings.tokenLabel(consent), tone: model.strings.tone(forToken: consent))
                    }
                }
                if let recovery = model.daemonState?.recoveryConsentStatus?["recovery_model"]?.stringValue {
                    HStack {
                        Text("\(model.strings.text(.recovery)):")
                        StatusBadge(text: model.strings.tokenLabel(recovery), tone: model.strings.tone(forToken: recovery))
                    }
                }
                stringList(
                    title: model.strings.text(.allowedCommands),
                    values: model.daemonState?.recoveryConsentStatus?["non_mutating_diagnostics"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                if let controlActions = model.daemonState?.recoveryConsentStatus?["control_recovery_actions"]?.arrayValue {
                    Text(model.strings.text(.activeSupervision)).bold()
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
                GroupBox(model.strings.text(.recoveryFlow)) {
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
                    .frame(maxWidth: .infinity, alignment: .leading)
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
                GroupBox(model.strings.text(.summaryCards)) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(model.daemonState?.launchagentSummary.plistPath ?? model.strings.text(.none))
                            .textSelection(.enabled)
                        HStack {
                            Text("\(model.strings.text(.loadedStatus)):")
                            if let loadedStatus = model.daemonState?.launchagentSummary.loadedStatus {
                                StatusBadge(text: model.strings.tokenLabel(loadedStatus), tone: model.strings.tone(forToken: loadedStatus))
                            } else {
                                Text(model.strings.text(.none))
                            }
                        }
                    }
                }
                commandDeck
                metadataGroup(title: model.strings.text(.statusDiagnostics), values: launchAgentStatusDiagnostics)
                if let stderrPreview = launchAgentStatusStderrPreview {
                    GroupBox(model.strings.text(.stderrPreview)) {
                        Text(stderrPreview)
                            .font(.system(.caption, design: .monospaced))
                            .textSelection(.enabled)
                            .lineLimit(6)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                HStack {
                    Button(model.strings.text(.openPlist)) {
                        model.openLaunchAgentPlist()
                    }
                    Button(model.strings.text(.openRuntime)) {
                        model.openRuntimeDirectory()
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
                    title: model.strings.text(.startActions),
                    tone: .caution,
                    commands: startCommands
                )
                commandDeckSection(
                    title: model.strings.text(.recoverActions),
                    tone: .critical,
                    commands: recoverCommands
                )
                commandDeckSection(
                    title: model.strings.text(.logActions),
                    tone: .neutral,
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
                metadataGroup(
                    title: model.strings.text(.programArguments),
                    values: model.daemonState?.launchagentPreview?["program_arguments"]?.arrayValue?.compactMap(\.stringValue) ?? []
                )
                metadataGroup(
                    title: model.strings.text(.previewMetadata),
                    values: previewMetadata
                )
                metadataGroup(
                    title: model.strings.text(.environmentAssumptions),
                    values: environmentAssumptions
                )
                metadataGroup(
                    title: model.strings.text(.logPaths),
                    values: logPaths
                )
                commandListGroup(
                    title: model.strings.text(.tailLogs),
                    commands: logTailCommands
                )
                HStack {
                    Button(model.strings.text(.copyStdoutTail)) {
                        model.copyLaunchAgentLogTailCommand(kind: "stdout")
                    }
                    Button(model.strings.text(.copyStderrTail)) {
                        model.copyLaunchAgentLogTailCommand(kind: "stderr")
                    }
                }
                if let plistXML = model.daemonState?.launchagentPreview?["plist_xml"]?.stringValue {
                    GroupBox(model.strings.text(.plistPreview)) {
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Spacer()
                                Button(model.strings.text(.copyPlist)) {
                                    model.copyLaunchAgentPlistXML()
                                }
                            }
                            Text(plistXML)
                                .font(.system(.caption, design: .monospaced))
                                .textSelection(.enabled)
                                .lineLimit(12)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
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
                    ForEach(values, id: \.self) { value in
                        Text("• \(value)")
                    }
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

    private var recoveryPreviews: some View {
        GroupBox(model.strings.text(.diagnosticPriority)) {
            VStack(alignment: .leading, spacing: 6) {
                diagnosticGroup(title: model.strings.text(.needsAttention), tone: .critical, items: needsAttentionDiagnostics)
                diagnosticGroup(title: model.strings.text(.verifyNow), tone: .caution, items: verifyNowDiagnostics)
                diagnosticGroup(title: model.strings.text(.healthySignals), tone: .positive, items: healthyDiagnostics)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var nextActions: some View {
        GroupBox(model.strings.text(.nextActions)) {
            Group {
                if (model.daemonState?.nextActions ?? []).isEmpty {
                    StateCardView(
                        icon: "checkmark.circle",
                        title: model.strings.text(.nextActions),
                        message: model.strings.text(.noNextActions),
                        tone: .positive,
                        badgeText: model.strings.text(.healthySignals),
                        actionTitle: model.strings.text(.refresh),
                        action: { Task { await model.refreshCurrentScreen() } }
                    )
                } else {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(model.daemonState?.nextActions ?? []) { action in
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    StatusBadge(text: actionPriorityTitle(action), tone: actionPriorityTone(action))
                                    Spacer()
                                }
                                commandRow(action.command)
                                if !action.reason.isEmpty {
                                    Text("\(model.strings.text(.reason)): \(action.reason)")
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func commandRow(_ command: String) -> some View {
        HStack(alignment: .top) {
            Text(command)
                .font(.system(.body, design: .monospaced))
                .textSelection(.enabled)
            Spacer(minLength: 12)
            Button(model.strings.text(.copyCommand)) {
                model.copyToClipboard(command, message: model.strings.text(.copiedCommand))
            }
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

    private var daemonFocusItems: [(title: String, summary: String, badge: String, tone: StatusTone, action: () -> Void)] {
        var items: [(String, String, String, StatusTone, () -> Void)] = []

        if let action = model.daemonState?.nextActions.first {
            items.append((
                model.strings.text(.reviewDaemonAction),
                action.reason.isEmpty ? action.command : action.reason,
                actionPriorityTitle(action),
                actionPriorityTone(action),
                { }
            ))
        }

        if let loadedStatus = model.daemonState?.launchagentSummary.loadedStatus {
            items.append((
                model.strings.text(.checkLaunchAgentStatus),
                model.strings.tokenLabel(loadedStatus),
                model.strings.text(.launchAgent),
                model.strings.tone(forToken: loadedStatus),
                {
                    showLaunchAgent = true
                }
            ))
        }

        if !preflightChecks.isEmpty {
            items.append((
                model.strings.text(.openRunbook),
                model.strings.text(.launchAgentRunbook),
                model.strings.text(.verification),
                .caution,
                {
                    showLaunchAgentRunbook = true
                }
            ))
        }

        return items
    }

    @ViewBuilder
    private func stringList(title: String, values: [String]) -> some View {
        if !values.isEmpty {
            VStack(alignment: .leading, spacing: 4) {
                Text(title).bold()
                ForEach(values, id: \.self) { value in
                    Text("• \(value)")
                }
            }
        }
    }

    @ViewBuilder
    private func diagnosticGroup(title: String, tone: StatusTone, items: [String]) -> some View {
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    StatusBadge(text: title, tone: tone)
                    Spacer()
                }
                ForEach(items, id: \.self) { item in
                    Text("• \(item)")
                }
            }
        }
    }

    @ViewBuilder
    private func commandDeckSection<ExtraButtons: View>(
        title: String,
        tone: StatusTone,
        commands: [String],
        @ViewBuilder extraButtons: () -> ExtraButtons = { EmptyView() }
    ) -> some View {
        if !commands.isEmpty || !(ExtraButtons.self == EmptyView.self) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    StatusBadge(text: title, tone: tone)
                    Spacer()
                }
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
        var values = verificationCommands(commands: model.daemonState?.launchagentSummary.launchctlCommands ?? [:])
        if let healthCheck = values.last, healthCheck.contains("/health") {
            values = Array(values.dropLast()) + [healthCheck]
        }
        return values
    }

    private var startCommands: [String] {
        let commands = model.daemonState?.launchagentSummary.launchctlCommands ?? [:]
        return ["bootstrap", "kickstart"].compactMap { commands[$0] }
    }

    private var recoverCommands: [String] {
        var values: [String] = []
        let commands = model.daemonState?.launchagentSummary.launchctlCommands ?? [:]
        if let bootout = commands["bootout"] {
            values.append(bootout)
        }
        values.append(contentsOf: model.daemonState?.nextActions.map(\.command).filter {
            $0.contains("repair") || $0.contains("cleanup") || $0.contains("bootout")
        } ?? [])
        return Array(NSOrderedSet(array: values)) as? [String] ?? values
    }

    private var logCommands: [String] {
        logTailCommands + logPaths
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

    private var troubleshootingNotes: [String] {
        model.strings.troubleshootingNotes()
    }

    private func actionPriorityTone(_ action: DaemonNextAction) -> StatusTone {
        let command = action.command
        if command.contains("repair") || command.contains("cleanup") || command.contains("bootout") {
            return .critical
        }
        if command.contains("start") || command.contains("bootstrap") || command.contains("kickstart") {
            return .caution
        }
        if command.contains("status") || command.contains("health") || command.contains("print") {
            return .positive
        }
        return .neutral
    }

    private func actionPriorityTitle(_ action: DaemonNextAction) -> String {
        switch actionPriorityTone(action) {
        case .critical: return model.strings.text(.needsAttention)
        case .caution: return model.strings.text(.suggestedAction)
        case .positive: return model.strings.text(.verifyNow)
        case .neutral: return model.strings.text(.actionSummary)
        }
    }

    private func daemonSummaryValue(_ card: SummaryCard) -> String {
        guard let value = card.value else {
            return model.strings.text(.none)
        }
        if let string = value.stringValue {
            return model.strings.summaryValueLabel(key: card.key, value: string)
        }
        return value.displayText
    }

    @ViewBuilder
    private func daemonSummaryValueView(_ card: SummaryCard) -> some View {
        if let string = card.value?.stringValue {
            StatusBadge(
                text: model.strings.summaryValueLabel(key: card.key, value: string),
                tone: model.strings.tone(forToken: string)
            )
        } else if let boolValue = card.value?.boolValue {
            StatusBadge(
                text: model.strings.booleanValueLabel(boolValue),
                tone: boolValue ? .positive : .critical
            )
        } else {
            Text(daemonSummaryValue(card)).font(.headline)
        }
    }
}

private struct FlowLayout<Data: RandomAccessCollection, ID: Hashable, Content: View>: View {
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
        HStack(spacing: spacing) {
            ForEach(Array(data), id: id) { element in
                content(element)
            }
        }
    }
}
