import Foundation

/// A phase of the interval workout. Shared between the app target and the
/// widget extension target (Live Activity), so this file's target
/// membership must include both.
enum IntervalPhase: String, Codable, Hashable {
    case prepare
    case work
    case rest
    case finished

    var displayName: String {
        switch self {
        case .prepare: return "準備"
        case .work: return "運動"
        case .rest: return "休憩"
        case .finished: return "完了"
        }
    }
}
