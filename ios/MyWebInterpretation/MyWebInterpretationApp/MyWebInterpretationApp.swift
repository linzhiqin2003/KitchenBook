import SwiftUI

@main
struct MyWebInterpretationApp: App {
    @StateObject private var authVM = AuthViewModel()

    var body: some Scene {
        WindowGroup {
            if authVM.isAuthenticated {
                ContentView(authVM: authVM)
            } else {
                AuthView(authVM: authVM)
            }
        }
    }
}
