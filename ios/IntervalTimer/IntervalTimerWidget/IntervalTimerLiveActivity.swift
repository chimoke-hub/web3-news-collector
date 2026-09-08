import ActivityKit
import WidgetKit
import SwiftUI

struct IntervalTimerLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: IntervalActivityAttributes.self) { context in
            LockScreenView(attributes: context.attributes, state: context.state)
                .activityBackgroundTint(color(for: context.state.phase).opacity(0.2))
                .activitySystemActionForegroundColor(.primary)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    Label(context.state.phase.displayName, systemImage: symbol(for: context.state.phase))
                        .font(.headline)
                        .foregroundStyle(color(for: context.state.phase))
                }
                DynamicIslandExpandedRegion(.trailing) {
                    countdownText(context.state)
                        .font(.title2.monospacedDigit())
                        .frame(width: 64)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(context.attributes.timerName)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        ProgressView(value: progress(context.state), total: 1)
                            .tint(color(for: context.state.phase))
                        Text("ラウンド \(context.state.currentRound) / \(context.state.totalRounds)")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            } compactLeading: {
                Image(systemName: symbol(for: context.state.phase))
                    .foregroundStyle(color(for: context.state.phase))
            } compactTrailing: {
                countdownText(context.state)
                    .font(.caption.monospacedDigit())
                    .frame(width: 40)
            } minimal: {
                Image(systemName: symbol(for: context.state.phase))
                    .foregroundStyle(color(for: context.state.phase))
            }
            .widgetURL(URL(string: "intervaltimer://open"))
            .keylineTint(color(for: context.state.phase))
        }
    }

    @ViewBuilder
    private func countdownText(_ state: IntervalActivityAttributes.ContentState) -> some View {
        if state.isPaused {
            Text(timeString(max(0, state.phaseEndDate.timeIntervalSinceNow)))
        } else {
            Text(timerInterval: Date.now...state.phaseEndDate, countsDown: true, showsHours: false)
        }
    }

    private func progress(_ state: IntervalActivityAttributes.ContentState) -> Double {
        guard state.phaseDuration > 0 else { return 0 }
        let elapsed = state.phaseDuration - max(0, state.phaseEndDate.timeIntervalSinceNow)
        return min(max(elapsed / state.phaseDuration, 0), 1)
    }

    private func symbol(for phase: IntervalPhase) -> String {
        switch phase {
        case .prepare: return "hourglass"
        case .work: return "flame.fill"
        case .rest: return "figure.cooldown"
        case .finished: return "checkmark.circle.fill"
        }
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

private struct LockScreenView: View {
    let attributes: IntervalActivityAttributes
    let state: IntervalActivityAttributes.ContentState

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Label(state.phase.displayName, systemImage: symbol)
                    .font(.headline)
                Spacer()
                if state.isPaused {
                    Text("一時停止中")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                } else {
                    Text(timerInterval: Date.now...state.phaseEndDate, countsDown: true, showsHours: false)
                        .font(.title.monospacedDigit())
                }
            }
            ProgressView(value: progress, total: 1)
            Text("\(attributes.timerName) ・ ラウンド \(state.currentRound)/\(state.totalRounds)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
    }

    private var progress: Double {
        guard state.phaseDuration > 0 else { return 0 }
        let elapsed = state.phaseDuration - max(0, state.phaseEndDate.timeIntervalSinceNow)
        return min(max(elapsed / state.phaseDuration, 0), 1)
    }

    private var symbol: String {
        switch state.phase {
        case .prepare: return "hourglass"
        case .work: return "flame.fill"
        case .rest: return "figure.cooldown"
        case .finished: return "checkmark.circle.fill"
        }
    }
}
