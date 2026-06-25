import AppKit
import SwiftUI

@MainActor
final class SayaneAppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        activatePreviewWindow(attemptsRemaining: 8)
    }

    private func activatePreviewWindow(attemptsRemaining: Int) {
        NSRunningApplication.current.activate(options: [.activateAllWindows])
        NSApp.activate(ignoringOtherApps: true)
        NSApp.windows.first?.makeKeyAndOrderFront(nil)
        guard attemptsRemaining > 0, NSApp.windows.first == nil else {
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { [attemptsRemaining] in
            self.activatePreviewWindow(attemptsRemaining: attemptsRemaining - 1)
        }
    }
}

@main
struct SayaneApp: App {
    @NSApplicationDelegateAdaptor(SayaneAppDelegate.self) private var appDelegate
    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            RootView(model: model)
                .frame(minWidth: 1080, minHeight: 720)
        }
        .windowResizability(.contentSize)
    }
}
