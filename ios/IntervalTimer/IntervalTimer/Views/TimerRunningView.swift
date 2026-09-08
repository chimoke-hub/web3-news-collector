import SwiftUI

struct TimerRunningView: View {
    @ObservedObject var engine: IntervalTimerEngine

    var body: some View {
        VStack(spacing: 24) {
            Text(engine.phase.displayName)
                .font(.title)
                .foregroundStyle(color(for: engine.phase))

            Text(timeString(engine.remaining))
                .font(.system(size: 72, weight: .bold, design: .rounded))
                .monospacedDigit()
                .animation(.default, value: engine.remaining)

            Text("ラウンド \(engine.currentRound) / \(engine.config.rounds)")
                .font(.headline)
                .foregroundStyle(.secondary)

            HStack(spacing: 32) {
                Button {
                    engine.runState == .running ? engine.pause() : engine.resume()
                } label: {
                    Image(systemName: engine.runState == .running ? "pause.fill" : "play.fill")
                        .font(.title)
                }

                Button {
                    engine.skipPhase()
                } label: {
                    Image(systemName: "forward.end.fill")
                        .font(.title)
                }

                Button(role: .destructive) {
                    engine.stop()
                } label: {
                    Image(systemName: "stop.fill")
                        .font(.title)
                }
            }
            .buttonStyle(.bordered)
        }
        .padding()
    }

    private func color(for phase: IntervalPhase) -> Color {
        switch phase {
        case .prepare: return .yellow
        case .work: return .red
        case .rest: return .blue
        case .finished: return .green
        }
    }

    private func timeString(_ interval: TimeInterval) -> String {
        let total = Int(interval.rounded(.up))
        return String(format: "%02d:%02d", total / 60, total % 60)
    }
}
