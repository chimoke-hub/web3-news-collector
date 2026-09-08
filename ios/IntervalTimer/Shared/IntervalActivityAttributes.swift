import Foundation
import ActivityKit

/// Attributes for the interval timer's Live Activity, rendered on the Lock
/// Screen and in the Dynamic Island. Shared between the app target and the
/// widget extension target, so this file's target membership must include
/// both.
struct IntervalActivityAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var phase: IntervalPhase
        /// The date the current phase ends. Combined with `Text(timerInterval:)`
        /// in the widget, the countdown updates live without any app or
        /// widget-extension code running.
        var phaseEndDate: Date
        var phaseDuration: TimeInterval
        var isPaused: Bool
        var currentRound: Int
        var totalRounds: Int
    }

    /// Fixed (non-updating) attributes for the activity's lifetime.
    var timerName: String
}
