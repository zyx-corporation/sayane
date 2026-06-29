import Foundation

struct BridgeConfiguration: Sendable {
    var host: String = "127.0.0.1"
    var port: Int = 38741
    var profileID: String = "default"

    var baseURL: URL {
        URL(string: "http://\(host):\(port)")!
    }

    var healthURL: URL {
        baseURL.appending(path: "/health")
    }

    var debugShellURL: URL {
        baseURL.appending(path: "/app/ui")
    }

    var tokenFileURL: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".sayane/bridge.token")
    }

    var logFileURL: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".sayane/run-app-local.log")
    }

    func bootstrapURL(token: String) -> URL {
        var components = URLComponents(url: baseURL.appending(path: "/app/ui"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "bootstrap_token", value: token)]
        return components.url!
    }

    func debugShellEntryURL(token: String?) -> URL {
        guard let token else { return debugShellURL }
        let trimmed = token.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return debugShellURL }
        return bootstrapURL(token: trimmed)
    }
}
