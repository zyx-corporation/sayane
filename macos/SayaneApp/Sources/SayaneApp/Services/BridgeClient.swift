import Foundation

enum BridgeError: LocalizedError, Sendable {
    case missingToken(URL)
    case invalidResponse
    case http(status: Int, detail: String?)
    case notConnected

    var errorDescription: String? {
        switch self {
        case let .missingToken(url): return "Missing bearer token at \(url.path)"
        case .invalidResponse: return "Invalid Bridge response"
        case let .http(status, detail): return "HTTP \(status): \(detail ?? "Unknown error")"
        case .notConnected: return "Could not connect to local Bridge"
        }
    }
}

actor BridgeClient {
    let configuration: BridgeConfiguration
    private let session: URLSession

    init(configuration: BridgeConfiguration = BridgeConfiguration()) {
        self.configuration = configuration
        let config = URLSessionConfiguration.default
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        self.session = URLSession(configuration: config)
    }

    func health() async throws -> HealthResponse {
        let request = URLRequest(url: configuration.baseURL.appending(path: "/health"))
        return try await decode(HealthResponse.self, request: request)
    }

    func contract() async throws -> AppContract {
        let request = try authorizedRequest(path: "/app/contract")
        return try await decode(AppContract.self, request: request)
    }

    func homeState() async throws -> HomeScreenState {
        let request = try authorizedRequest(path: "/app/screen-state/home")
        return try await decode(HomeScreenState.self, request: request)
    }

    func queueState() async throws -> CandidateQueueScreenState {
        let request = try authorizedRequest(path: "/app/screen-state/candidates")
        return try await decode(CandidateQueueScreenState.self, request: request)
    }

    func detailState(candidateID: String) async throws -> CandidateDetailScreenState {
        let request = try authorizedRequest(path: "/app/screen-state/candidates/\(candidateID)")
        return try await decode(CandidateDetailScreenState.self, request: request)
    }

    func diffState(candidateID: String) async throws -> CandidateDiffPayload {
        let request = try authorizedRequest(path: "/app/candidates/\(candidateID)/diff")
        return try await decode(CandidateDiffPayload.self, request: request)
    }

    func lineageState(candidateID: String) async throws -> CandidateLineagePayload {
        let request = try authorizedRequest(path: "/app/candidates/\(candidateID)/lineage")
        return try await decode(CandidateLineagePayload.self, request: request)
    }

    func daemonState() async throws -> DaemonPanelScreenState {
        let request = try authorizedRequest(path: "/app/screen-state/daemon")
        return try await decode(DaemonPanelScreenState.self, request: request)
    }

    func openVaultSession(level: String, purpose: String, profileID: String) async throws -> VaultSessionStatus {
        var request = try authorizedRequest(path: "/app/vault-session/open", method: "POST")
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(
            VaultSessionOpenRequestBody(level: level, purpose: purpose, profileId: profileID)
        )
        return try await decode(VaultSessionStatus.self, request: request)
    }

    func lockVaultSessions(sessionID: String? = nil, closeAll: Bool = false) async throws -> VaultSessionStatus {
        var request = try authorizedRequest(path: "/app/vault-session/lock", method: "POST")
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(
            VaultSessionLockRequestBody(sessionID: sessionID, closeAll: closeAll)
        )
        return try await decode(VaultSessionStatus.self, request: request)
    }

    func captureClipboard(text: String, locale: String?) async throws -> CandidateMutationResponse {
        let body = CaptureRequestBody(content: text, profileId: configuration.profileID, locale: locale)
        var request = try authorizedRequest(path: "/app/capture-clipboard", method: "POST")
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)
        return try await decode(CandidateMutationResponse.self, request: request)
    }

    func evaluate(candidateID: String, level: Int = 1) async throws -> CandidateMutationResponse {
        var request = try authorizedRequest(path: "/app/candidates/\(candidateID)/evaluate", method: "POST")
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(EvaluateRequestBody(level: level))
        return try await decode(CandidateMutationResponse.self, request: request)
    }

    func approve(candidateID: String, forceCritical: Bool = false, overrideReason: String? = nil) async throws -> CandidateMutationResponse {
        var request = try authorizedRequest(path: "/app/candidates/\(candidateID)/approve", method: "POST")
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(ApproveRequestBody(forceCritical: forceCritical, overrideReason: overrideReason))
        return try await decode(CandidateMutationResponse.self, request: request)
    }

    func reject(candidateID: String, reason: String?) async throws -> CandidateMutationResponse {
        var request = try authorizedRequest(path: "/app/candidates/\(candidateID)/reject", method: "POST")
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(RejectRequestBody(reason: reason))
        return try await decode(CandidateMutationResponse.self, request: request)
    }

    func revise(candidateID: String, editedText: String, targetSection: String?, changeReason: String?) async throws -> CandidateMutationResponse {
        var request = try authorizedRequest(path: "/app/candidates/\(candidateID)/revise", method: "POST")
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(ReviseRequestBody(editedText: editedText, targetSection: targetSection, changeReason: changeReason))
        return try await decode(CandidateMutationResponse.self, request: request)
    }

    func resetSession() async {
        HTTPCookieStorage.shared.cookies?.forEach(HTTPCookieStorage.shared.deleteCookie)
    }

    private func loadToken() throws -> String {
        let tokenURL = configuration.tokenFileURL
        guard FileManager.default.fileExists(atPath: tokenURL.path) else {
            throw BridgeError.missingToken(tokenURL)
        }
        return try String(contentsOf: tokenURL).trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func authorizedRequest(path: String, method: String = "GET") throws -> URLRequest {
        let token = try loadToken()
        var request = URLRequest(url: configuration.baseURL.appending(path: path))
        request.httpMethod = method
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        return request
    }

    private func decode<T: Decodable>(_ type: T.Type, request: URLRequest) async throws -> T {
        let data = try await data(for: request)
        let decoder = JSONDecoder()
        return try decoder.decode(T.self, from: data)
    }

    private func data(for request: URLRequest) async throws -> Data {
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw BridgeError.invalidResponse
            }
            guard (200..<300).contains(http.statusCode) else {
                let detail = try? JSONDecoder().decode([String: String].self, from: data)["detail"]
                throw BridgeError.http(status: http.statusCode, detail: detail)
            }
            return data
        } catch let error as BridgeError {
            throw error
        } catch {
            throw BridgeError.notConnected
        }
    }
}
