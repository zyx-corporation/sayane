// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "SayaneApp",
    platforms: [
        .macOS(.v14),
    ],
    products: [
        .executable(name: "SayaneApp", targets: ["SayaneApp"]),
    ],
    targets: [
        .executableTarget(
            name: "SayaneApp",
            path: "Sources/SayaneApp"
        ),
        .testTarget(
            name: "SayaneAppTests",
            dependencies: ["SayaneApp"],
            path: "Tests/SayaneAppTests"
        ),
    ]
)
