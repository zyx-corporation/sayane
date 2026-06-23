import Foundation

struct HealthResponse: Codable, Sendable {
    let status: String
    let version: String?
    let sourceUpdatedAt: String?
    let component: String?

    private enum CodingKeys: String, CodingKey {
        case status, version, component
        case sourceUpdatedAt = "source_updated_at"
    }
}

struct CandidateQueueScreenState: Codable, Sendable {
    let kind: String
    let reviewableCount: Int
    let statusCounts: [String: Int]
    let topSections: [TopSection]
    let items: [CandidateItem]

    private enum CodingKeys: String, CodingKey {
        case kind, items
        case reviewableCount = "reviewable_count"
        case statusCounts = "status_counts"
        case topSections = "top_sections"
    }
}

struct TopSection: Codable, Hashable, Sendable, Identifiable {
    var id: String { section }
    let section: String
    let count: Int
}

struct CandidateItem: Codable, Hashable, Sendable, Identifiable {
    let id: String
    let status: String?
    let section: String?
    let content: String?
    let displaySummary: String?
    let proposalSection: String?
    let capturedAt: String?

    private enum CodingKeys: String, CodingKey {
        case id, status, section, content
        case displaySummary = "display_summary"
        case proposalSection = "proposal_section"
        case capturedAt = "captured_at"
    }
}

struct CandidateDetailScreenState: Codable, Sendable {
    let kind: String
    let uiSummary: CandidateUISummary
    let allowedActions: CandidateAllowedActions
    let proposal: [String: JSONValue]
    let evaluation: [String: JSONValue]
    let content: String?
    let diffAvailable: Bool

    private enum CodingKeys: String, CodingKey {
        case kind, proposal, evaluation, content
        case uiSummary = "ui_summary"
        case allowedActions = "allowed_actions"
        case diffAvailable = "diff_available"
    }
}

struct CandidateUISummary: Codable, Sendable {
    let status: String?
    let section: String?
    let operation: String?
    let sourceType: String?
    let evaluationLevel: Int?
    let rdeClass: String?
    let canApprove: Bool?

    private enum CodingKeys: String, CodingKey {
        case status, section, operation
        case sourceType = "source_type"
        case evaluationLevel = "evaluation_level"
        case rdeClass = "rde_class"
        case canApprove = "can_approve"
    }
}

struct CandidateAllowedActions: Codable, Sendable {
    let evaluate: Bool
    let approve: Bool
    let reject: Bool
    let revise: Bool
    let showDiff: Bool

    private enum CodingKeys: String, CodingKey {
        case evaluate, approve, reject, revise
        case showDiff = "show_diff"
    }
}

struct CandidateDiffPayload: Codable, Sendable {
    let reviewSurface: String?
    let section: String?
    let recommendedSection: String?
    let profileUpdateRecommended: Bool?
    let hasDuplicates: Bool?
    let add: [String]?
    let remove: [String]?
    let alreadyPresent: [String]?
    let note: String?
    let uiSummary: [String: JSONValue]?
    let listDiff: [String: JSONValue]?

    private enum CodingKeys: String, CodingKey {
        case section, add, remove, note
        case reviewSurface = "review_surface"
        case recommendedSection = "recommended_section"
        case profileUpdateRecommended = "profile_update_recommended"
        case hasDuplicates = "has_duplicates"
        case alreadyPresent = "already_present"
        case uiSummary = "ui_summary"
        case listDiff = "list_diff"
    }
}

struct HomeScreenState: Codable, Sendable {
    let kind: String
    let summaryCards: [SummaryCard]
    let topReviewItems: [TopReviewItem]
    let topDaemonActions: [String]
    let quickLinks: [QuickLink]

    private enum CodingKeys: String, CodingKey {
        case kind
        case summaryCards = "summary_cards"
        case topReviewItems = "top_review_items"
        case topDaemonActions = "top_daemon_actions"
        case quickLinks = "quick_links"
    }
}

struct SummaryCard: Codable, Hashable, Sendable, Identifiable {
    var id: String { key }
    let key: String
    let value: JSONValue?
}

struct TopReviewItem: Codable, Hashable, Sendable, Identifiable {
    var id: String { candidateId }
    let candidateId: String
    let status: String?
    let proposalSection: String?
    let displaySummary: String?
    let requiresReview: Bool?

    private enum CodingKeys: String, CodingKey {
        case status
        case candidateId = "candidate_id"
        case proposalSection = "proposal_section"
        case displaySummary = "display_summary"
        case requiresReview = "requires_review"
    }
}

struct QuickLink: Codable, Hashable, Sendable, Identifiable {
    var id: String { path }
    let screen: String
    let path: String
}

struct DaemonPanelScreenState: Codable, Sendable {
    let kind: String
    let summaryCards: [SummaryCard]
    let operatorPanels: [OperatorPanel]
    let serviceTargetSummary: ServiceTargetSummary
    let launchagentSummary: LaunchAgentSummary
    let operatorPhaseSummary: OperatorPhaseSummary
    let operatorPhaseDetails: OperatorPhaseDetails
    let nextActions: [DaemonNextAction]
    let runtimeInit: [String: JSONValue]
    let cleanupPreview: [String: JSONValue]
    let repairPreview: [String: JSONValue]
    let launchagentPreview: [String: JSONValue]?
    let launchagentStatus: [String: JSONValue]?
    let packagingStatus: [String: JSONValue]?
    let serviceControlBoundary: [String: JSONValue]?
    let serviceTargetsStatus: [String: JSONValue]?
    let supervisionStatus: [String: JSONValue]?
    let recoveryConsentStatus: [String: JSONValue]?
    let operatorPhaseStatus: [String: JSONValue]?

    private enum CodingKeys: String, CodingKey {
        case kind
        case summaryCards = "summary_cards"
        case operatorPanels = "operator_panels"
        case serviceTargetSummary = "service_target_summary"
        case launchagentSummary = "launchagent_summary"
        case operatorPhaseSummary = "operator_phase_summary"
        case operatorPhaseDetails = "operator_phase_details"
        case nextActions = "next_actions"
        case runtimeInit = "runtime_init"
        case cleanupPreview = "cleanup_preview"
        case repairPreview = "repair_preview"
        case launchagentPreview = "launchagent_preview"
        case launchagentStatus = "launchagent_status"
        case packagingStatus = "packaging_status"
        case serviceControlBoundary = "service_control_boundary"
        case serviceTargetsStatus = "service_targets_status"
        case supervisionStatus = "supervision_status"
        case recoveryConsentStatus = "recovery_consent_status"
        case operatorPhaseStatus = "operator_phase_status"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        kind = try container.decode(String.self, forKey: .kind)
        summaryCards = try container.decode([SummaryCard].self, forKey: .summaryCards)
        operatorPanels = try container.decode([OperatorPanel].self, forKey: .operatorPanels)
        serviceTargetSummary = try container.decode(ServiceTargetSummary.self, forKey: .serviceTargetSummary)
        launchagentSummary = try container.decode(LaunchAgentSummary.self, forKey: .launchagentSummary)
        operatorPhaseSummary = try container.decode(OperatorPhaseSummary.self, forKey: .operatorPhaseSummary)
        operatorPhaseDetails = try container.decode(OperatorPhaseDetails.self, forKey: .operatorPhaseDetails)
        nextActions = try container.decodeIfPresent([DaemonNextAction].self, forKey: .nextActions) ?? []
        runtimeInit = try container.decodeIfPresent([String: JSONValue].self, forKey: .runtimeInit) ?? [:]
        cleanupPreview = try container.decodeIfPresent([String: JSONValue].self, forKey: .cleanupPreview) ?? [:]
        repairPreview = try container.decodeIfPresent([String: JSONValue].self, forKey: .repairPreview) ?? [:]
        launchagentPreview = try container.decodeIfPresent([String: JSONValue].self, forKey: .launchagentPreview)
        launchagentStatus = try container.decodeIfPresent([String: JSONValue].self, forKey: .launchagentStatus)
        packagingStatus = try container.decodeIfPresent([String: JSONValue].self, forKey: .packagingStatus)
        serviceControlBoundary = try container.decodeIfPresent([String: JSONValue].self, forKey: .serviceControlBoundary)
        serviceTargetsStatus = try container.decodeIfPresent([String: JSONValue].self, forKey: .serviceTargetsStatus)
        supervisionStatus = try container.decodeIfPresent([String: JSONValue].self, forKey: .supervisionStatus)
        recoveryConsentStatus = try container.decodeIfPresent([String: JSONValue].self, forKey: .recoveryConsentStatus)
        operatorPhaseStatus = try container.decodeIfPresent([String: JSONValue].self, forKey: .operatorPhaseStatus)
    }
}

struct DaemonNextAction: Codable, Hashable, Sendable, Identifiable {
    var id: String { "\(command)::\(reason)" }
    let command: String
    let reason: String

    init(command: String, reason: String) {
        self.command = command
        self.reason = reason
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let value = try? container.decode(String.self) {
            self.init(command: value, reason: "")
            return
        }
        let keyed = try decoder.container(keyedBy: CodingKeys.self)
        self.init(
            command: try keyed.decode(String.self, forKey: .command),
            reason: try keyed.decodeIfPresent(String.self, forKey: .reason) ?? ""
        )
    }

    private enum CodingKeys: String, CodingKey {
        case command
        case reason
    }
}

struct OperatorPanel: Codable, Hashable, Sendable, Identifiable {
    var id: String { panel }
    let panel: String
    let title: String?
    let status: String?
    let highlights: [String]?
    let commands: [String]?
    let deferredCommands: [String]?
    let recommendedFlow: [String]?

    private enum CodingKeys: String, CodingKey {
        case panel, title, status, highlights, commands
        case deferredCommands = "deferred_commands"
        case recommendedFlow = "recommended_flow"
    }
}

struct ServiceTargetSummary: Codable, Sendable {
    let currentPlatform: String?
    let recommendedTarget: String?
    let targets: [ServiceTarget]

    private enum CodingKeys: String, CodingKey {
        case targets
        case currentPlatform = "current_platform"
        case recommendedTarget = "recommended_target"
    }
}

struct ServiceTarget: Codable, Hashable, Sendable, Identifiable {
    var id: String { target }
    let target: String
    let status: String?
    let notes: [String]?
}

struct LaunchAgentSummary: Codable, Sendable {
    let previewAvailable: Bool
    let statusAvailable: Bool
    let plistPath: String?
    let loadedStatus: String?
    let launchctlCommands: [String: String]?

    private enum CodingKeys: String, CodingKey {
        case plistPath = "plist_path"
        case loadedStatus = "loaded_status"
        case launchctlCommands = "launchctl_commands"
        case previewAvailable = "preview_available"
        case statusAvailable = "status_available"
    }
}

struct OperatorPhaseSummary: Codable, Sendable {
    let phase: String?
    let phaseStatus: String?
    let phaseReadiness: String?
    let blockingReasons: [String]
    let checklist: [String]

    private enum CodingKeys: String, CodingKey {
        case phase
        case phaseStatus = "phase_status"
        case phaseReadiness = "phase_readiness"
        case blockingReasons = "blocking_reasons"
        case checklist
    }
}

struct OperatorPhaseDetails: Codable, Sendable {
    let currentSupportedOperatorPath: CurrentSupportedOperatorPath
    let workstreams: [Workstream]
    let recommendedImplementationOrder: [String]
    let readSurfaces: [String]
    let exitCriteria: [String]
    let notInScope: [String]

    private enum CodingKeys: String, CodingKey {
        case currentSupportedOperatorPath = "current_supported_operator_path"
        case workstreams
        case recommendedImplementationOrder = "recommended_implementation_order"
        case readSurfaces = "read_surfaces"
        case exitCriteria = "exit_criteria"
        case notInScope = "not_in_scope"
    }
}

struct CurrentSupportedOperatorPath: Codable, Sendable {
    let startupCommandText: String?
    let bootstrapUI: String?
    let localOnly: Bool?
    let notes: [String]

    private enum CodingKeys: String, CodingKey {
        case startupCommandText = "startup_command_text"
        case bootstrapUI = "bootstrap_ui"
        case localOnly = "local_only"
        case notes
    }
}

struct Workstream: Codable, Hashable, Sendable, Identifiable {
    var id: String { name }
    let name: String
    let status: String?
    let detail: String?
}

struct CandidateLineagePayload: Codable, Sendable {
    let candidateId: String
    let lineageEntries: [LineageEntry]?
    let raw: [String: JSONValue]?

    private enum CodingKeys: String, CodingKey {
        case raw
        case candidateId = "candidate_id"
        case lineageEntries = "lineage_entries"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let object = try? container.decode([String: JSONValue].self) {
            raw = object
            candidateId = object["candidate_id"]?.stringValue ?? ""
            lineageEntries = object["lineage_entries"]?.arrayValue?.compactMap { value in
                guard case let .object(obj) = value else { return nil }
                return LineageEntry(
                    summary: obj["summary"]?.stringValue ?? obj["status"]?.stringValue ?? obj["id"]?.stringValue ?? "entry",
                    details: obj.mapValues(\.displayText)
                )
            }
        } else {
            raw = nil
            let keyed = try decoder.container(keyedBy: CodingKeys.self)
            candidateId = try keyed.decode(String.self, forKey: .candidateId)
            lineageEntries = try keyed.decodeIfPresent([LineageEntry].self, forKey: .lineageEntries)
        }
    }
}

struct LineageEntry: Codable, Hashable, Sendable, Identifiable {
    var id: String { summary }
    let summary: String
    let details: [String: String]
}

struct AppContract: Codable, Sendable {
    let kind: String
    let preferredEntrypoint: String

    private enum CodingKeys: String, CodingKey {
        case kind
        case preferredEntrypoint = "preferred_entrypoint"
    }
}

struct CandidateMutationResponse: Codable, Sendable {
    let id: String
    let status: String
    let reviewSurface: String?

    private enum CodingKeys: String, CodingKey {
        case id, status
        case reviewSurface = "review_surface"
    }
}

struct CaptureRequestBody: Codable, Sendable {
    let content: String
    let profileId: String
    let locale: String?

    init(content: String, profileId: String = "default", locale: String? = nil) {
        self.content = content
        self.profileId = profileId
        self.locale = locale
    }

    private enum CodingKeys: String, CodingKey {
        case content, locale
        case profileId = "profile_id"
    }
}

struct EvaluateRequestBody: Codable, Sendable {
    let level: Int
}

struct ApproveRequestBody: Codable, Sendable {
    let forceCritical: Bool
    let overrideReason: String?

    init(forceCritical: Bool = false, overrideReason: String? = nil) {
        self.forceCritical = forceCritical
        self.overrideReason = overrideReason
    }

    private enum CodingKeys: String, CodingKey {
        case overrideReason = "override_reason"
        case forceCritical = "force_critical"
    }
}

struct RejectRequestBody: Codable, Sendable {
    let reason: String?
}

struct ReviseRequestBody: Codable, Sendable {
    let editedText: String
    let targetSection: String?
    let changeReason: String?

    private enum CodingKeys: String, CodingKey {
        case editedText = "edited_text"
        case targetSection = "target_section"
        case changeReason = "change_reason"
    }
}
