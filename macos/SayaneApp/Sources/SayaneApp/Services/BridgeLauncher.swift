import Foundation

enum BridgeLauncherError: LocalizedError {
    case repoRootNotFound
    case cliNotFound
    case launcherMissing(URL)
    case launchFailed(String)

    var errorDescription: String? {
        switch self {
        case .repoRootNotFound:
            return "Could not locate the Sayane repository root from the current working directory."
        case .cliNotFound:
            return "Could not find an installed Sayane CLI. Install it first with curl+bash or pip, then retry."
        case let .launcherMissing(url):
            return "Missing launcher script: \(url.path)"
        case let .launchFailed(message):
            return "Bridge launch failed: \(message)\nCheck ~/.sayane/run-app-local.log."
        }
    }
}

struct BridgeLauncher {
    static func launchDiagnosticSummary(
        startingAt startURL: URL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath),
        environment: [String: String] = ProcessInfo.processInfo.environment,
        homeDirectory: URL = FileManager.default.homeDirectoryForCurrentUser,
        resourceURL: URL? = Bundle.main.resourceURL
    ) -> String {
        if let helperURL = resolveBundledHelperURL(resourceURL: resourceURL) {
            return "bundled_helper: \(helperURL.path)"
        }
        if let cliURL = resolveInstalledCLIURL(environment: environment, homeDirectory: homeDirectory) {
            return "installed_cli: \(cliURL.path)"
        }
        if let repoRoot = resolveRepoRoot(startingAt: startURL) {
            return "repo_launcher: \(repoRoot.appendingPathComponent("scripts/run-app-local.sh").path)"
        }
        return "unavailable"
    }

    static func resolveBundledHelperURL(resourceURL: URL? = Bundle.main.resourceURL) -> URL? {
        guard let resourceURL else { return nil }
        let candidate = resourceURL.appendingPathComponent("run-bridge-helper.sh")
        return FileManager.default.isExecutableFile(atPath: candidate.path) ? candidate : nil
    }

    static func canLaunchBridge(
        startingAt startURL: URL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath),
        environment: [String: String] = ProcessInfo.processInfo.environment,
        homeDirectory: URL = FileManager.default.homeDirectoryForCurrentUser
    ) -> Bool {
        resolveBundledHelperURL() != nil
            || resolveInstalledCLIURL(environment: environment, homeDirectory: homeDirectory) != nil
            || resolveRepoRoot(startingAt: startURL) != nil
    }

    static func resolveInstalledCLIURL(
        environment: [String: String] = ProcessInfo.processInfo.environment,
        homeDirectory: URL = FileManager.default.homeDirectoryForCurrentUser
    ) -> URL? {
        let fm = FileManager.default
        let explicit = environment["SAYANE_CLI_BIN"].map(URL.init(fileURLWithPath:))
        let pathEntries = (environment["PATH"] ?? "")
            .split(separator: ":")
            .map { URL(fileURLWithPath: String($0)).appendingPathComponent("sayane") }
        let candidates = [
            explicit,
            homeDirectory.appendingPathComponent(".local/bin/sayane"),
            URL(fileURLWithPath: "/opt/homebrew/bin/sayane"),
            URL(fileURLWithPath: "/usr/local/bin/sayane"),
            URL(fileURLWithPath: "/usr/bin/sayane"),
        ]
        .compactMap { $0 } + pathEntries

        for candidate in candidates {
            if fm.isExecutableFile(atPath: candidate.path) {
                return candidate
            }
        }
        return nil
    }

    static func resolveRepoRoot(startingAt startURL: URL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)) -> URL? {
        var current = startURL.standardizedFileURL
        let fm = FileManager.default
        while true {
            let candidate = current.appendingPathComponent("scripts/run-app-local.sh")
            if fm.fileExists(atPath: candidate.path) {
                return current
            }
            let parent = current.deletingLastPathComponent()
            if parent.path == current.path { break }
            current = parent
        }
        return nil
    }

    private static func logFileURL(homeDirectory: URL = FileManager.default.homeDirectoryForCurrentUser) -> URL {
        homeDirectory.appendingPathComponent(".sayane/run-app-local.log")
    }

    private static func launchBundledHelper(_ helperURL: URL) throws {
        let process = Process()
        process.executableURL = helperURL
        process.currentDirectoryURL = FileManager.default.homeDirectoryForCurrentUser
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        try process.run()
        process.waitUntilExit()
        if process.terminationStatus != 0 {
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let message = String(data: data, encoding: .utf8) ?? "unknown error"
            throw BridgeLauncherError.launchFailed(message)
        }
    }

    private static func launchInstalledCLI(
        cliURL: URL,
        environment: [String: String] = ProcessInfo.processInfo.environment,
        homeDirectory: URL = FileManager.default.homeDirectoryForCurrentUser
    ) throws {
        let fm = FileManager.default
        let sayaneDir = homeDirectory.appendingPathComponent(".sayane", isDirectory: true)
        try fm.createDirectory(at: sayaneDir, withIntermediateDirectories: true)

        let profilePath = sayaneDir
            .appendingPathComponent("profiles/default/sayane.profile.yaml")
            .path
        let logPath = logFileURL(homeDirectory: homeDirectory).path
        let cliPath = cliURL.path.replacingOccurrences(of: "'", with: "'\\''")
        let script = """
        set -euo pipefail
        mkdir -p "$HOME/.sayane"
        if [ ! -f '\(profilePath.replacingOccurrences(of: "'", with: "'\\''"))' ]; then
          '\(cliPath)' init >> '\(logPath.replacingOccurrences(of: "'", with: "'\\''"))' 2>&1 || true
        fi
        if lsof -tiTCP:38741 -sTCP:LISTEN >/dev/null 2>&1; then
          exit 0
        fi
        nohup '\(cliPath)' serve --host 127.0.0.1 --port 38741 >> '\(logPath.replacingOccurrences(of: "'", with: "'\\''"))' 2>&1 </dev/null &
        """

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = ["-lc", script]
        process.currentDirectoryURL = homeDirectory
        process.environment = environment
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        try process.run()
        process.waitUntilExit()
        if process.terminationStatus != 0 {
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let message = String(data: data, encoding: .utf8) ?? "unknown error"
            throw BridgeLauncherError.launchFailed(message)
        }
    }

    static func launchBridge(startingAt startURL: URL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)) throws {
        if let helperURL = resolveBundledHelperURL() {
            try launchBundledHelper(helperURL)
            return
        }
        if let cliURL = resolveInstalledCLIURL() {
            try launchInstalledCLI(cliURL: cliURL)
            return
        }

        guard let repoRoot = resolveRepoRoot(startingAt: startURL) else {
            throw BridgeLauncherError.cliNotFound
        }
        let launcherURL = repoRoot.appendingPathComponent("scripts/run-app-local.sh")
        guard FileManager.default.isExecutableFile(atPath: launcherURL.path) else {
            throw BridgeLauncherError.launcherMissing(launcherURL)
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = [launcherURL.path, "--no-open", "--no-init"]
        process.currentDirectoryURL = repoRoot
        process.standardInput = FileHandle.nullDevice
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        try process.run()
        process.waitUntilExit()
        if process.terminationStatus != 0 {
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let message = String(data: data, encoding: .utf8) ?? "unknown error"
            throw BridgeLauncherError.launchFailed(message)
        }
    }
}
