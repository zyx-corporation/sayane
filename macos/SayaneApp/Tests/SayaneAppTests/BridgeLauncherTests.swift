import Foundation
import Testing
@testable import SayaneApp

@Test func resolveRepoRootFindsRepositoryFromPackageTree() {
    let start = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        .appendingPathComponent("macos/SayaneApp/Sources/SayaneApp")
    let repoRoot = BridgeLauncher.resolveRepoRoot(startingAt: start)
    #expect(repoRoot != nil)
    #expect(repoRoot?.lastPathComponent == "sayane")
}
