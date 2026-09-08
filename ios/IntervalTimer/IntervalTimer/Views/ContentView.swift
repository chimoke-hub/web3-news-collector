import SwiftUI

struct ContentView: View {
    @StateObject private var engine = IntervalTimerEngine()
    @State private var config = IntervalTimerConfig()
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            Group {
                switch engine.runState {
                case .idle, .finished:
                    TimerConfigView(config: $config, engine: engine)
                case .running, .paused:
                    TimerRunningView(engine: engine)
                }
            }
            .navigationTitle(config.name)
        }
        .onChange(of: scenePhase) { newPhase in
            if newPhase == .active {
                engine.reconcileAfterForeground()
            }
        }
        .task {
            IntervalNotificationScheduler().requestAuthorization()
        }
    }
}

#Preview {
    ContentView()
}
