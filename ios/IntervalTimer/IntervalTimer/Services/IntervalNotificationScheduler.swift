import Foundation
import UserNotifications

/// Schedules local notifications for every remaining phase transition, as a
/// fallback that fires even if the background-audio keep-alive gets
/// throttled or the process is terminated by the system.
struct IntervalNotificationScheduler {
    private let center = UNUserNotificationCenter.current()
    private let idsKey = "interval-timer-notification-ids"

    func requestAuthorization() {
        center.requestAuthorization(options: [.alert, .sound]) { _, error in
            if let error {
                print("Notification authorization failed: \(error)")
            }
        }
    }

    /// Schedules a notification for every remaining phase transition,
    /// starting from the end of `currentPhase` (round `currentRound`) at
    /// `currentPhaseEndDate`. Call again (it cancels prior pending ones
    /// first) whenever the anchor changes: on start, on resume from pause,
    /// and after a manual skip.
    func schedule(config: IntervalTimerConfig, currentPhase: IntervalPhase, currentRound: Int, currentPhaseEndDate: Date) {
        cancelAll()
        let transitions = Self.upcomingTransitions(
            config: config,
            from: currentPhase,
            round: currentRound,
            phaseEndDate: currentPhaseEndDate
        )

        var identifiers: [String] = []
        for transition in transitions {
            let content = UNMutableNotificationContent()
            content.title = config.name
            content.body = "\(transition.round)/\(config.rounds) \(transition.phase.displayName)"
            content.sound = .default
            let interval = max(transition.date.timeIntervalSinceNow, 0.1)
            let trigger = UNTimeIntervalNotificationTrigger(timeInterval: interval, repeats: false)
            let id = UUID().uuidString
            identifiers.append(id)
            center.add(UNNotificationRequest(identifier: id, content: content, trigger: trigger))
        }
        UserDefaults.standard.set(identifiers, forKey: idsKey)
    }

    func cancelAll() {
        let ids = UserDefaults.standard.stringArray(forKey: idsKey) ?? []
        if !ids.isEmpty {
            center.removePendingNotificationRequests(withIdentifiers: ids)
        }
        UserDefaults.standard.removeObject(forKey: idsKey)
    }

    struct Transition {
        let phase: IntervalPhase
        let round: Int
        let date: Date
    }

    /// Walks the phase state machine forward from the given point, mirroring
    /// `IntervalTimerEngine.advancePhase()`'s transition rules exactly, and
    /// returns every future (phase, round, date) transition through
    /// `.finished`.
    static func upcomingTransitions(config: IntervalTimerConfig, from phase: IntervalPhase, round: Int, phaseEndDate: Date) -> [Transition] {
        var results: [Transition] = []
        var cursor = phaseEndDate
        var currentPhase = phase
        var currentRound = round

        while currentPhase != .finished {
            let next: IntervalPhase
            let nextRound: Int
            switch currentPhase {
            case .prepare:
                next = .work
                nextRound = currentRound
            case .work:
                if currentRound >= config.rounds {
                    next = .finished
                    nextRound = currentRound
                } else if config.restSeconds > 0 {
                    next = .rest
                    nextRound = currentRound
                } else {
                    next = .work
                    nextRound = currentRound + 1
                }
            case .rest:
                next = .work
                nextRound = currentRound + 1
            case .finished:
                next = .finished
                nextRound = currentRound
            }

            results.append(Transition(phase: next, round: nextRound, date: cursor))
            if next == .finished { break }
            cursor = cursor.addingTimeInterval(config.duration(for: next))
            currentPhase = next
            currentRound = nextRound
        }
        return results
    }
}
