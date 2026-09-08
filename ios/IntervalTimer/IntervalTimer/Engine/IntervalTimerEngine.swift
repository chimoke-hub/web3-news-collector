import Foundation
import Combine

/// Drives the interval workout state machine off wall-clock dates (not a
/// naive decrementing counter), so it stays correct across app suspension:
/// `phaseEndDate` is always the source of truth, and `reconcileAfterForeground()`
/// catches up any transitions missed while the process was backgrounded.
@MainActor
final class IntervalTimerEngine: ObservableObject {
    enum RunState: Equatable {
        case idle
        case running
        case paused
        case finished
    }

    @Published private(set) var runState: RunState = .idle
    @Published private(set) var phase: IntervalPhase = .prepare
    @Published private(set) var currentRound: Int = 1
    @Published private(set) var remaining: TimeInterval = 0

    private(set) var config: IntervalTimerConfig = IntervalTimerConfig()
    private(set) var phaseEndDate: Date = .now
    private(set) var phaseDuration: TimeInterval = 0

    private var uiTicker: Timer?
    private var pausedRemaining: TimeInterval = 0

    private let liveActivity = LiveActivityController()
    private let notifications = IntervalNotificationScheduler()
    private let audioKeepAlive = BackgroundAudioKeepAlive()
    private let soundPlayer = SoundPlayer()

    func configure(_ config: IntervalTimerConfig) {
        guard runState == .idle || runState == .finished else { return }
        self.config = config
    }

    func start() {
        guard runState == .idle || runState == .finished else { return }
        currentRound = 1
        let initialPhase: IntervalPhase = config.prepareSeconds > 0 ? .prepare : .work
        beginPhase(initialPhase, round: currentRound)
        runState = .running

        audioKeepAlive.start()
        notifications.schedule(config: config, currentPhase: phase, currentRound: currentRound, currentPhaseEndDate: phaseEndDate)
        Task { await liveActivity.start(timerName: config.name, state: makeState(isPaused: false)) }
        startTicker()
    }

    func pause() {
        guard runState == .running else { return }
        runState = .paused
        pausedRemaining = max(0, phaseEndDate.timeIntervalSinceNow)
        stopTicker()
        notifications.cancelAll()
        Task { await liveActivity.update(makeState(isPaused: true)) }
    }

    func resume() {
        guard runState == .paused else { return }
        phaseEndDate = Date().addingTimeInterval(pausedRemaining)
        runState = .running
        notifications.schedule(config: config, currentPhase: phase, currentRound: currentRound, currentPhaseEndDate: phaseEndDate)
        Task { await liveActivity.update(makeState(isPaused: false)) }
        startTicker()
    }

    func stop() {
        runState = .idle
        stopTicker()
        notifications.cancelAll()
        audioKeepAlive.stop()
        Task { await liveActivity.end() }
    }

    /// Manually advance to the next phase (round) ahead of schedule.
    func skipPhase() {
        guard runState == .running else { return }
        advancePhase()
        guard runState == .running else { return }
        notifications.schedule(config: config, currentPhase: phase, currentRound: currentRound, currentPhaseEndDate: phaseEndDate)
    }

    /// Call when the app returns to the foreground to catch up on any
    /// phase transitions that happened while the process was suspended.
    func reconcileAfterForeground() {
        guard runState == .running else { return }
        while runState == .running && phaseEndDate.timeIntervalSinceNow <= 0 {
            advancePhase()
        }
        refreshRemaining()
    }

    private func beginPhase(_ phase: IntervalPhase, round: Int) {
        self.phase = phase
        self.currentRound = round
        self.phaseDuration = config.duration(for: phase)
        self.phaseEndDate = Date().addingTimeInterval(phaseDuration)
        self.remaining = phaseDuration
    }

    private func advancePhase() {
        switch phase {
        case .prepare:
            beginPhase(.work, round: currentRound)
        case .work:
            if currentRound >= config.rounds {
                beginPhase(.finished, round: currentRound)
                finish()
                return
            } else if config.restSeconds > 0 {
                beginPhase(.rest, round: currentRound)
            } else {
                beginPhase(.work, round: currentRound + 1)
            }
        case .rest:
            beginPhase(.work, round: currentRound + 1)
        case .finished:
            return
        }
        soundPlayer.playTransition(for: phase)
        Task { await liveActivity.update(makeState(isPaused: false)) }
    }

    private func finish() {
        runState = .finished
        stopTicker()
        audioKeepAlive.stop()
        notifications.cancelAll()
        soundPlayer.playFinish()
        Task { await liveActivity.finish(makeState(isPaused: false)) }
    }

    private func startTicker() {
        stopTicker()
        let timer = Timer(timeInterval: 0.2, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.tick() }
        }
        RunLoop.main.add(timer, forMode: .common)
        uiTicker = timer
    }

    private func stopTicker() {
        uiTicker?.invalidate()
        uiTicker = nil
    }

    private func tick() {
        guard runState == .running else { return }
        if phaseEndDate.timeIntervalSinceNow <= 0 {
            advancePhase()
        }
        refreshRemaining()
    }

    private func refreshRemaining() {
        remaining = max(0, phaseEndDate.timeIntervalSinceNow)
    }

    private func makeState(isPaused: Bool) -> IntervalActivityAttributes.ContentState {
        .init(
            phase: phase,
            phaseEndDate: phaseEndDate,
            phaseDuration: phaseDuration,
            isPaused: isPaused,
            currentRound: currentRound,
            totalRounds: config.rounds
        )
    }
}
