import Foundation

enum BridgeLauncherError: LocalizedError {
    case repoRootNotFound
    case launcherMissing(URL)
    case launchFailed(String)

    var errorDescription: String? {
        switch self {
        case .repoRootNotFound:
            return "Could not locate the Sayane repository root from the current working directory."
        case let .launcherMissing(url):
            return "Missing launcher script: \(url.path)"
        case let .launchFailed(message):
            return "Bridge launch failed: \(message)"
        }
    }
}

struct BridgeLauncher {
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

    static func launchBridge(startingAt startURL: URL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)) throws {
        guard let repoRoot = resolveRepoRoot(startingAt: startURL) else {
            throw BridgeLauncherError.repoRootNotFound
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
