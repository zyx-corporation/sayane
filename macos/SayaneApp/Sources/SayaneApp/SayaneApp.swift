import AppKit
import SwiftUI

@MainActor
enum WindowSizing {
    static let minimumWindowWidth: CGFloat = 1000
    static let minimumWindowHeight: CGFloat = 160

    static func fitAllWindows() {
        for window in NSApp.windows {
            fit(window)
        }
    }

    static func fit(_ window: NSWindow) {
        guard let contentView = window.contentView else { return }
        contentView.layoutSubtreeIfNeeded()
        let fitting = contentView.fittingSize
        guard fitting.width > 0, fitting.height > 0 else { return }
        window.minSize = NSSize(width: minimumWindowWidth, height: minimumWindowHeight)
        window.setContentSize(
            NSSize(
                width: max(minimumWindowWidth, fitting.width),
                height: max(minimumWindowHeight, fitting.height)
            )
        )
    }
}

@MainActor
final class SayaneAppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        activateAppWindow(attemptsRemaining: 8)
    }

    private func activateAppWindow(attemptsRemaining: Int) {
        NSRunningApplication.current.activate(options: [.activateAllWindows])
        NSApp.activate(ignoringOtherApps: true)
        NSApp.unhide(nil)
        for window in NSApp.windows {
            window.deminiaturize(nil)
            window.orderFrontRegardless()
            WindowSizing.fit(window)
        }
        NSApp.windows.first?.makeKeyAndOrderFront(nil)
        guard attemptsRemaining > 0, NSApp.windows.first == nil else {
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { [attemptsRemaining] in
            self.activateAppWindow(attemptsRemaining: attemptsRemaining - 1)
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
                .frame(minWidth: WindowSizing.minimumWindowWidth)
        }
        .windowResizability(.contentSize)
    }
}
