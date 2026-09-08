import Foundation
import ActivityKit

/// Thin wrapper around the app's single `IntervalActivityAttributes` Live
/// Activity, so `IntervalTimerEngine` doesn't need to touch ActivityKit
/// directly.
@MainActor
final class LiveActivityController {
    private var activity: Activity<IntervalActivityAttributes>?

    func start(timerName: String, state: IntervalActivityAttributes.ContentState) async {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }
        if activity != nil {
            await end()
        }
        let attributes = IntervalActivityAttributes(timerName: timerName)
        do {
            activity = try Activity.request(
                attributes: attributes,
                content: .init(state: state, staleDate: nil)
            )
        } catch {
            print("Live Activity start failed: \(error)")
        }
    }

    func update(_ state: IntervalActivityAttributes.ContentState) async {
        guard let activity else { return }
        await activity.update(.init(state: state, staleDate: nil))
    }

    /// Updates to the final state, then ends the activity after a short
    /// delay so the user sees the "完了" state instead of it vanishing.
    func finish(_ state: IntervalActivityAttributes.ContentState) async {
        guard let activity else { return }
        await activity.update(.init(state: state, staleDate: nil))
        try? await Task.sleep(for: .seconds(3))
        await activity.end(activity.content, dismissalPolicy: .default)
        self.activity = nil
    }

    func end() async {
        guard let activity else { return }
        await activity.end(activity.content, dismissalPolicy: .immediate)
        self.activity = nil
    }
}
