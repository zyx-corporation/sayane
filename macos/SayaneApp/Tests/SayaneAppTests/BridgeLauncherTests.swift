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

@Test func resolveInstalledCLIPrefersExplicitEnvironment() {
    let temp = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString)
    try? FileManager.default.createDirectory(at: temp, withIntermediateDirectories: true)
    let cli = temp.appendingPathComponent("sayane")
    FileManager.default.createFile(atPath: cli.path, contents: Data("#!/bin/sh\n".utf8))
    try? FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: cli.path)

    let resolved = BridgeLauncher.resolveInstalledCLIURL(
        environment: ["SAYANE_CLI_BIN": cli.path],
        homeDirectory: FileManager.default.homeDirectoryForCurrentUser
    )
    #expect(resolved?.path == cli.path)
}

@Test func resolveInstalledCLIFindsUserLocalShim() {
    let tempHome = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString)
    let localBin = tempHome.appendingPathComponent(".local/bin", isDirectory: true)
    try? FileManager.default.createDirectory(at: localBin, withIntermediateDirectories: true)
    let cli = localBin.appendingPathComponent("sayane")
    FileManager.default.createFile(atPath: cli.path, contents: Data("#!/bin/sh\n".utf8))
    try? FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: cli.path)

    let resolved = BridgeLauncher.resolveInstalledCLIURL(
        environment: ["PATH": ""],
        homeDirectory: tempHome
    )
    #expect(resolved?.path == cli.path)
}

@Test func canLaunchBridgeUsesInstalledCLI() {
    let tempHome = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString)
    let localBin = tempHome.appendingPathComponent(".local/bin", isDirectory: true)
    try? FileManager.default.createDirectory(at: localBin, withIntermediateDirectories: true)
    let cli = localBin.appendingPathComponent("sayane")
    FileManager.default.createFile(atPath: cli.path, contents: Data("#!/bin/sh\n".utf8))
    try? FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: cli.path)

    #expect(BridgeLauncher.canLaunchBridge(
        startingAt: URL(fileURLWithPath: "/tmp/no-repo"),
        environment: ["PATH": ""],
        homeDirectory: tempHome
    ))
}

@Test func resolveBundledHelperFindsExecutableScript() {
    let tempResources = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try? FileManager.default.createDirectory(at: tempResources, withIntermediateDirectories: true)
    let helper = tempResources.appendingPathComponent("run-bridge-helper.sh")
    FileManager.default.createFile(atPath: helper.path, contents: Data("#!/bin/sh\n".utf8))
    try? FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: helper.path)

    let resolved = BridgeLauncher.resolveBundledHelperURL(resourceURL: tempResources)
    #expect(resolved?.path == helper.path)
}

@Test func launchDiagnosticSummaryPrefersBundledHelper() {
    let tempResources = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try? FileManager.default.createDirectory(at: tempResources, withIntermediateDirectories: true)
    let helper = tempResources.appendingPathComponent("run-bridge-helper.sh")
    FileManager.default.createFile(atPath: helper.path, contents: Data("#!/bin/sh\n".utf8))
    try? FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: helper.path)

    let summary = BridgeLauncher.launchDiagnosticSummary(
        startingAt: URL(fileURLWithPath: "/tmp/no-repo"),
        environment: ["PATH": ""],
        homeDirectory: FileManager.default.homeDirectoryForCurrentUser,
        resourceURL: tempResources
    )
    #expect(summary.contains("bundled_helper:"))
    #expect(summary.contains(helper.path))
}
