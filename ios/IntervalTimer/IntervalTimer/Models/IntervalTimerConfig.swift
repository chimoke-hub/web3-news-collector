import Foundation

/// User-configurable shape of a workout: prepare countdown, work/rest
/// durations, and number of rounds.
struct IntervalTimerConfig: Codable, Equatable {
    var name: String = "インターバルタイマー"
    var prepareSeconds: Int = 5
    var workSeconds: Int = 30
    var restSeconds: Int = 15
    var rounds: Int = 8

    func duration(for phase: IntervalPhase) -> TimeInterval {
        switch phase {
        case .prepare: return TimeInterval(prepareSeconds)
        case .work: return TimeInterval(workSeconds)
        case .rest: return TimeInterval(restSeconds)
        case .finished: return 0
        }
    }
}
